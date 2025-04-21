from .apps import AIModelConfig
from .processes.JobRecommendation import *
from .processes.DomainPrediction import *
from .processes.responseValidator import *
from .processes.generate_PDF import *

from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, Http404, HttpResponseServerError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.utils.dateparse import parse_date, parse_datetime
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.decorators import api_view
from pdf2image import convert_from_path
from django.views.decorators.cache import never_cache

from .models import *
from .serializers import *
from .utils import *

import secrets
import string
import os, bcrypt
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
from pathlib import Path

import json
from io import BytesIO
import shutil
import tempfile

import layoutparser as lp
import fitz
import groq

from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

ocrModel = lp.TesseractAgent()

# Thread Pool for Uploading Files
executor = ThreadPoolExecutor(max_workers=5)

# Thread Pool for Training Model
model_executor = ThreadPoolExecutor(max_workers=10)

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(blurred)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    opened = cv2.morphologyEx(equalized, cv2.MORPH_OPEN, kernel, iterations=1)
    sharpening_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(opened, -1, sharpening_kernel)
    return sharpened


def pre_process_files(file_path):
    
    enhanced_images = []
    if file_path.endswith(".pdf"):
        images = convert_from_path(file_path)
        images = list(
            map(lambda img: img.convert("RGB") if img.mode != "RGB" else img, images)
        )
        for image in images:
            img_array = np.array(image)
            enhanced_img = preprocess_image(img_array)
            enhanced_images.append(Image.fromarray(enhanced_img))
    else:
        enhanced_images = [Image.open(file_path)]
    
    return enhanced_images


def getBoundingBox(json_output):
    wordBoxes = []
    word_info = dict()
    for page in json_output.get("pages", []):
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                for word in line.get("words", []):
                    word_geometry = word.get("geometry", [])

                    # Convert tuples to lists for modification
                    word_geometry = [list(coord) for coord in word_geometry]

                    word_geometry[0][0] *= 1000
                    word_geometry[0][1] *= 1000
                    word_geometry[1][0] *= 1000
                    word_geometry[1][1] *= 1000

                    x1 = int(word_geometry[0][0])
                    x2 = int(word_geometry[0][1])
                    x3 = int(word_geometry[1][0])
                    x4 = int(word_geometry[1][1])

                    word_info = {"word": word.get("value"), "box": [x1, x2, x3, x4]}

                    wordBoxes.append(word_info)
    return wordBoxes

def getLoggedInUser(request):
    login_id = request.session.get('login_id')

    if login_id is None:
        return HttpResponse("Please login or signup", status=401)
    else:
        user = Login.objects.get(pk=login_id)
        if user:
            return user
        else:
            return HttpResponse("User does not exist", status=403)
        
def table_exists(image_path: str) -> bool:
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        return False

    result = AIModelConfig.yoloModel.predict(img, verbose=False)[0]
    table_class_id = next((k for k, v in result.names.items() if v.lower() == "table"), None)
    if table_class_id is None:
        return False

    return any(int(box.cls[0]) == table_class_id for box in result.boxes)

# Function to process the document in the background
def process_document(file_id, file_path):
    
    newFile = File.objects.get(pk=file_id)
    try:
        file_name = file_path.stem
        fileDirPath = file_path.parent

        # Open the PDF file
        pdf_document = fitz.open(str(file_path))
        allPageData = []
        table_exists_flag = False

        # Convert each page to an image
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Render page as a pixmap (image)
            pix = page.get_pixmap(dpi=300)  # Set high DPI for better quality
            
            # Convert to PIL Image and save
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            image_path = fileDirPath / f"{file_name}_{page_num + 1}.png"
            img.save(image_path)
            
            res = ocrModel.detect(img, return_response=True)
            allPageData.append(res["text"])

            # Call table_exists
            if not table_exists_flag:  # Only run until first table is found
                table_exists_flag = table_exists(str(image_path))

        # Update the File entry with the total number of pages and status
        newFile.ocrText = " ".join(allPageData)
        newFile.totalPages = len(pdf_document)
        newFile.fileStatus = "Uploaded"
        newFile.hasTable = table_exists_flag  
        newFile.save()

        resumeInsights(newFile.pk)
        predictDomainAndRoles(newFile.pk)

    except Exception as e:
        print(e)
        newFile.fileStatus = "Failed"
        newFile.save()

@api_view(["GET"])
def getThumbnailImage(request, fileId):
    try:
        # Get the file object (assuming it's already validated)
        fileObj = File.objects.get(pk=fileId)

        # Define your file path (replace with your actual file path logic)
        file_name, file_ext = Path(fileObj.filename).stem, Path(fileObj.filename).suffix
        
        # Generate your image path (example: 'AppUserFiles/userId/fileId/filename.png')
        fileDirPath = Path(StaticData.objects.get(key="FilePath").value) / str(fileObj.userId.pk) / str(fileId)
        imagePath = fileDirPath / (f"{file_name}_1.png" if file_ext == '.pdf' else fileObj.filename)  # Example path to your image file

        # Ensure the file exists
        if not os.path.exists(imagePath):
            return HttpResponse("Image file not found", status=404)

        # Open the image file
        with open(imagePath, 'rb') as image_file:
            # Read the file content into memory (bytes)
            image_data = image_file.read()

        # Create an in-memory image for the response
        image_io = BytesIO(image_data)

        # Check image extension to determine the content type
        if imagePath.suffix.lower() in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif imagePath.suffix.lower() == '.png':
            content_type = 'image/png'
        else:
            return HttpResponse("Unsupported image type", status=400)

        # Return the image as a FileResponse
        return FileResponse(image_io, content_type=content_type)

    except File.DoesNotExist:
        return HttpResponse("File not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    
@api_view(["GET"])
def getCoverFile(request, fileId):
    try:
        # Get the file object (assuming it's already validated)
        fileObj = File.objects.get(pk=fileId)

        # Define your file path (replace with your actual file path logic)
        file_name, file_ext = Path(fileObj.filename).stem, Path(fileObj.filename).suffix
        
        # Generate your image path (example: 'AppUserFiles/userId/fileId/filename.png')
        fileDirPath = Path(StaticData.objects.get(key="FilePath").value) / str(fileObj.userId.pk) / str(fileId)
        filePath = fileDirPath / fileObj.filename  # Example path to your image file

        # Ensure the file exists
        if not os.path.exists(filePath):
            return HttpResponse("Image file not found", status=404)

        # Determine correct content type
        if file_ext in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif file_ext == ".png":
            content_type = "image/png"
        elif file_ext == ".pdf":
            content_type = "application/pdf"
        else:
            return HttpResponse("Unsupported file type", status=400)
        
        # Open the image file
        with open(filePath, 'rb') as resume_file:
            # Read the file content into memory (bytes)
            data = resume_file.read()

        # Create an in-memory image for the response
        fileBytes = BytesIO(data)

        return FileResponse(fileBytes, content_type=content_type)

    except File.DoesNotExist:
        return HttpResponse("File not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

@api_view(['POST'])
def upload_file(request):
    try:
        user = getLoggedInUser(request)

        if type(user) is not Login:
            return user

        userDirPath = Path(StaticData.objects.get(key='FilePath').value) / str(user.pk)

        uploaded_files = request.FILES.getlist("file")
        
        addedOn = timezone.now()

        for uploaded_file in uploaded_files:
            
            base_filename = Path(uploaded_file.name).stem
            file_extension = Path(uploaded_file.name).suffix

            # Check if a file with the same name exists in the project
            file_exists = File.objects.filter(userId=user.pk, filename=uploaded_file.name).exists()
            duplicate_count = 1
            new_filename = uploaded_file.name

            while file_exists:
                # Generate new filename by adding a count (e.g., filename(1).txt)
                new_filename = f"{base_filename}({duplicate_count}){file_extension}"
                file_exists = File.objects.filter(userId=user.pk, filename=new_filename).exists()
                duplicate_count += 1

            newFile = File.objects.create(
                userId=user,
                filename=new_filename,
                addedOn=addedOn,
                fileStatus="Processing"  # Set initial status to "Processing"
            )

            newFile.save()

            fileDirPath = userDirPath / str(newFile.pk)
            fileDirPath.mkdir(parents=True, exist_ok=True)

            fs = FileSystemStorage(location=fileDirPath, base_url=fileDirPath)
            fileLoc = fs.save(new_filename, uploaded_file)

            # Start the document processing in a separate thread
            executor.submit(process_document, newFile.pk, (fileDirPath / fileLoc))

        return HttpResponse("Success", status=200)

    except Exception as err:
        print(err)
        return HttpResponseServerError(err.args[0])
    
@api_view(['PUT'])
def retryUpload(request, fileId):
    try:
        user = getLoggedInUser(request)

        if type(user) is not Login:
            return user

        fileObj = File.objects.get(pk=fileId)
        fileDirPath = Path(StaticData.objects.get(key='FilePath').value) / str(fileObj.userId.pk) / str(fileId)

        file_path = fileDirPath / fileObj.filename

        # Start the document processing in a separate thread
        executor.submit(process_document, fileObj.pk, file_path)

        fileObj.refresh_from_db(fields=['fileStatus'])
        return HttpResponse(fileObj.fileStatus, status=200)

    except Exception as err:
        print(err)
        return HttpResponseServerError(err.args[0])

def generateAuthToken():
    characters = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(characters) for _ in range(30))
    return token

@api_view(['POST'])
def signup(request):
    try:
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        email_lower = email.lower()
        password = request.POST.get('password')
        
        if Login.objects.filter(email=email_lower):
            messages.error(request, 'Email Id already exists.')
            return JsonResponse({'success': False, 'error': 'Email Id already exists'})
        
        else:
            salt = bcrypt.gensalt()
            password_bytes = password.encode('utf-8')
            hashed_password = bcrypt.hashpw(password_bytes,salt)
            hashed_password_string = str(hashed_password,'UTF-8')
            token = generateAuthToken()
            
            Login.objects.create(
                username = username,
                email = email_lower,
                password = hashed_password_string,
                authToken=token
            )
        
            print('Account created')
            file_path = 'FilePath'
            folder_path = StaticData.objects.get(key=file_path).value
            user_id = Login.objects.get(email=email_lower).pk
            
            # Create user directory if it doesn't exist
            (Path(folder_path) / str(user_id)).mkdir(parents=True, exist_ok=True)

            return JsonResponse({'success': True, 'error': 'Account created Successfully'})
        
    except Exception as e:
        print(e)
        return JsonResponse({'success': False, 'error': 'Failed to create Account'})
        
@api_view(['POST'])
def login(request):
    try:
        
        email = request.POST['email']
        password = request.POST['password']
        password_bytes = password.encode('utf-8')
        email_lower = email.lower()
        print(password)
        print(email)
        user_data = Login.objects.filter(email=email_lower).values_list('email','password','id')
        if user_data:
            userId = user_data[0][2]
            print(userId)
            userPassword = user_data[0][1]
            print(userPassword)
            isvalid = bcrypt.checkpw(password_bytes,userPassword.encode('utf-8'))
            if isvalid:
                request.session['login_id'] = userId
                
                return JsonResponse({'success': True, 'error': 'Login sucessful'})
            else:
                return JsonResponse({'success': False, 'error': 'Incorrect Password','input':'Password'})
        else:
            return JsonResponse({'success': False, 'error': 'User does not exist','input':'Email'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Error in logging In'})

@api_view(['GET'])    
def getUserDetails(request):
    login_id = request.session.get('login_id')
    print(login_id)

    try:
        user = Login.objects.get(pk=login_id)
        files = user.files.all()
        
        # Serialize the files querysets
        total_files = FileSerializer(files, many=True).data
        total_completed = FileSerializer(files.filter(fileStatus="Validated"), many=True).data
        total_pending = FileSerializer(files.filter(fileStatus__in=['Tagged', 'Un-Tagged', 'Processing']), many=True).data

        userDet = {
            "id": user.pk,
            "email": user.email,
            "name": user.username,
            "userKey": user.authToken,
            "totalFiles": total_files,
            "totalCompleted": total_completed,
            "totalPending": total_pending
        }
        
        return JsonResponse(userDet, safe=False)
    except Login.DoesNotExist:
        err = UIMsg("Invalid User", "No such user exists")                   
        return HttpResponse(err, status=400)
    
@api_view(['GET'])
def logout(request):
    try:
        # Delete the login_id from session
        del request.session["login_id"]
        request.session.modified = True
        request.session.flush()

        return JsonResponse({'message': 'Logged out successfully'}, status=200)

    except KeyError:
        # Handle the case where the session key doesn't exist
        return JsonResponse({'error': 'No active session'}, status=400)

@api_view(["GET"])
def landing_page(request):
    return render(request, "index.html")  # your new landing page

@api_view(['GET'])
def login_page(request):
    return render(request, "login.html")

def set_cache_control(response):
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@api_view(["GET"])
def index_page(request):
    if not request.session.get('login_id'):
        return redirect('login_page')  # Redirect to login if not authenticated
    response = render(request, "main.html")
    return set_cache_control(response)

@never_cache
@api_view(['GET'])
def dynamic_template_view(request, page_name):
    
    if not request.session.get('login_id'):
        return redirect('login_page')  # Redirect to login if not authenticated

    # Construct the template name based on the page_name
    template_name = f'{page_name}.html'
    
    print(template_name)
    
    # Check if the template exists or raise a 404
    try:
        response = render(request, template_name)
        return set_cache_control(response)
    except:
        raise Http404(f'Template {template_name} not found')

@api_view(["DELETE"])
def delete_file(request, fileId):
    try:
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        file = File.objects.get(pk=fileId)
        fileDirectory = Path(StaticData.objects.get(key='FilePath').value) / str(file.userId.pk) / str(file.pk)
        
        shutil.rmtree(fileDirectory)
        file.delete()
        msg = UIMsg("Successful",  "File deleted successfully")                   
        return HttpResponse(msg, status=200)

    except File.DoesNotExist:
        err = UIMsg("Error in deleting",  "File not found")                   
        return HttpResponse(err, status=404)
    
    except Exception as e:
        err = UIMsg("Error in deleting",  str(e))                   
        return HttpResponse(err, status=500)
    
@api_view(["PUT"])
def setValidatedStatus(request, fileId):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        fileObj = File.objects.get(pk=fileId)
        
        if fileObj.userId.pk != user.pk:
            return HttpResponse("You are forbidden to access to this file", status=403)
        
        fileObj.fileStatus = "Validated"
        fileObj.save()
        
        return HttpResponse("File status updated to Validated", status=200)
    except File.DoesNotExist:
        return HttpResponse("File not found", status=404)
    except Exception as e:
        return HttpResponse(str(e), status=500)
    
@api_view(["GET"])
def searchFiles(request):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')
        status = request.GET.get('status')  # This will now be a comma-separated string

        # Apply filters
        files = File.objects.filter(userId=user.pk).order_by("-id")

        # Apply date filters if they exist
        if from_date:
            from_date = parse_datetime(from_date)
            files = files.filter(addedOn__gte=from_date)
        if to_date:
            to_date = parse_datetime(to_date)
            files = files.filter(addedOn__lte=to_date)

        # Apply status filters if the status string is not empty
        if status:
            status_filters = status.split(',')  # Split the comma-separated string
            files = files.filter(fileStatus__in=status_filters)
                
        serializer = FileSerializer(files, many=True)
        
        return JsonResponse(serializer.data, safe=False)
    except Exception as e:
        return HttpResponse(str(e), status=500)
    

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# -------------------------------- RESUME INSIGHTS -------------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
def resumeInsights(fileId):
        
    fileObj = File.objects.filter(pk=fileId)
    if fileObj.exists():
        resumeInsightsObj = ResumeInsights.objects.filter(fileId=fileId)
        
        if not resumeInsightsObj.exists():
            file = fileObj.first()
            resumeInsightsPrompt = f"""
            Extract structured information from the following resume text and return it strictly as a valid JSON object with no additional text or formatting. Ensure no markdown, backticks, or additional text:
            {{
                "Name": "",
                "Email": "",
                "Phone": "",
                "Address": "",
                "Skills": ["", "", ""],
                "Experience": [
                    {{
                        "Role": "",
                        "Company": "",
                        "Location": "",
                        "StartDate": "",
                        "EndDate": "",
                        "Description": ""
                    }}
                ],
                "Education": [
                    {{
                        "Degree": "",
                        "Institute": "",
                        "Year": "",
                        "Score": ""
                    }}
                ],
                "Projects": [
                    {{
                        "Name": "",
                        "Year": "",
                        "Description": ""
                    }}
                ],
                "Certifications": [
                    {{
                        "Name": "",
                        "IssuedBy": "",
                        "Date": ""
                    }}
                ]
            }}
            
            Resume Text:
            {file.ocrText}
            """

            client = groq.Client(api_key=AIModelConfig.apiKey1)

            resumeInsightsResponse = client.chat.completions.create(
            model=AIModelConfig.LLM,
            messages=[{"role": "system", "content": "You are an AI that extracts structured resume data in JSON format strictly without any extra formatting."},
                        {"role": "user", "content": resumeInsightsPrompt}],
            temperature=0.5,
            max_tokens=2000
            )

            resumeInsightsJson = json.loads(resumeInsightsResponse.choices[0].message.content)

            # Save to database
            ResumeInsights.objects.create(
                fileId=file,
                name=resumeInsightsJson.get("Name", ""),
                email=resumeInsightsJson.get("Email", ""),
                phone=resumeInsightsJson.get("Phone", ""),
                skills=resumeInsightsJson.get("Skills", []),
                experience=resumeInsightsJson.get("Experience", []),
                education=resumeInsightsJson.get("Education", []),
                projects=resumeInsightsJson.get("Projects", []),
                certifications=resumeInsightsJson.get("Certifications", []),
            )
        
    
@api_view(["GET"])
def getResumeInsights(request, fileId):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        resumeInsightsObj = ResumeInsights.objects.filter(fileId=fileId)

        if not resumeInsightsObj.exists():
            return HttpResponse("Insights not found", status=404)
        
        resumeInsight = resumeInsightsObj.first()

        return JsonResponse(ResumeInsightsSerializer(resumeInsight).data, safe=False)
    
    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)
    
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# ------------------------------- DOMAIN PREDICTION -----------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
def nicheRoles(domain, skills, experience):
    # Define the prompt dynamically
    nichePrompt = f"""
    Based on the following domain, skills and experience, suggest 3-5 niche job roles that are trustworthy and available in the practical world:

    Domain: {domain}
    Skills: {skills}
    Experience: {experience}

    Provide the response as a strict comma separated job roles without any extra text.
    Format: A,B,C
    """

    client = groq.Client(api_key=AIModelConfig.apiKey1)

    # Call the Groq API using Qwen model
    nicheResponse = client.chat.completions.create(
        model=AIModelConfig.LLM,
        messages=[{"role": "user", "content": nichePrompt}],
        temperature=1,
        max_tokens=4096
    )

    # Extract and process response to ensure strict list output
    nicheRoles = nicheResponse.choices[0].message.content
    jobRoles = nicheRoles.split(",")
    return jobRoles

def predictDomainUsingLLM(inputResume):

    categories = AIModelConfig.categories

    domainPredictionPrompt = f"""
    You are an AI model that analyzes resume text and predicts the professional domain of the candidate.

    Based on the resume provided below, identify the most relevant domain **strictly from the following list**:

    {categories}

    Return the domain name **exactly as it appears in the list above**, in **all caps**, with **no explanation**, **no extra formatting**, and **no JSON**, just a **single string** response.

    Resume Text:
    {inputResume}
    """

    client = groq.Client(api_key=AIModelConfig.apiKey2)

    domainPredictionResponse = client.chat.completions.create(
        model=AIModelConfig.LLM,
        messages=[
            {"role": "system", "content": "You are an AI that classifies resumes into one of the predefined categories."},
            {"role": "user", "content": domainPredictionPrompt}
        ],
        temperature=0.3,
        max_tokens=50
    )

    return domainPredictionResponse.choices[0].message.content.strip()


def predictDomainUsingModel(inputResume):
    predicted_category_index = predict_category(inputResume, AIModelConfig.domainModel, AIModelConfig.domainTokenizer, AIModelConfig.MAX_LEN)
    return AIModelConfig.categories[predicted_category_index]


def predictDomainAndRoles(fileId):
          
    fileObj = File.objects.filter(pk=fileId)

    if fileObj.exists():
        file = fileObj.first()

        inputResume = file.ocrText

        if(file.hasTable):
            domain = predictDomainUsingLLM(inputResume)
            print(f"LLM DOMAIN: {domain}")

        else:
            domain = predictDomainUsingModel(inputResume)
            print(f"Model DOMAIN: {domain}")

        resumeInsightsObj = ResumeInsights.objects.filter(fileId=fileId)

        if resumeInsightsObj.exists():
                 
            resumeInsight = resumeInsightsObj.first()

            skills = resumeInsight.skills
            experience = resumeInsight.experience

            roles = nicheRoles(domain, skills, experience)

            resumeInsight.domain = domain
            resumeInsight.roles = roles  # Store roles as JSON string
            resumeInsight.save()
   
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# ------------------------------ PREDICT PERSONALITY -----------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
def getModelPersonality(user_input):
    """
    Predicts the user's personality type based on their trait scores
    and generates a detailed, user-friendly explanation.

    :param user_input: Dictionary containing scores for 
                        'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'
    :return: String containing the personality report
    """

    # Convert user input into NumPy array and scale it
    user_features = np.array([[user_input["openness"], user_input["conscientiousness"], 
                               user_input["extraversion"], user_input["agreeableness"], 
                               user_input["neuroticism"]]])
    
    user_features_scaled = AIModelConfig.personalityScaler.transform(user_features)

    # Predict Personality Type
    prediction = AIModelConfig.personalityModel.predict(user_features_scaled)
    predicted_personality = AIModelConfig.personalityEncoder.inverse_transform(prediction)[0]

    return predicted_personality

def personalityInsights(clusterAverages, userInput, personality):
    personalityPrompt = f"""
    I have train a personality prediction model using the Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) to predict personality types based on these traits.
    The model uses a Random Forest Classifier and has been trained on a dataset of personality trait scores and their corresponding personality types.

    The model has predicted the user's personality type as: {personality}

    User has input the following trait scores:
    {userInput}

    Also i had clustered the personality types into 4 clusters based on the trait averages, the clusters average are as follows:
    {clusterAverages}

    Based on the user input and cluster averages,provide a detailed explanation of the user's personality type and why has the personality type been predicted.

    The explaination should be user-friendly and easy to understand, it should not contain any technical jargon.

    Based on the above data, provide the strengths, weaknesses, areas of improvement, and suggestions for the user to improve their personality traits.

    Provide your output in a JSON format.

    The structure of the JSON should be as follows:

    {{"personalityType": [the personality type predicted for the user by the model],
        "explanation": [the detailed explanation of the user's personality type],
        "strengths": [the strengths of the user's personality type],
        "weaknesses": [the weaknesses of the user's personality type],
        "areasOfImprovement": [the areas where the user can improve their personality traits],
        "suggestions": [suggestions to help the user improve their personality traits],
        "preferrableWorkEnvironment": [the preferrable work environment for the user based on their personality type],
        "reasoning": [the reasoning behind the prediction of the user's personality type (based on the user input and cluster averages). Dont mention the technical details of the model and anything about the clustering algorithm.]}}
    """

    client = groq.Client(api_key=AIModelConfig.apiKey2)

    personalityResponse = client.chat.completions.create(
    model=AIModelConfig.LLM,
    messages=[{"role": "system", "content": "You are an AI that extracts structured resume data in JSON format strictly without any extra formatting."},
              {"role": "user", "content": personalityPrompt}],
    temperature=0.7,
    max_tokens=1500
    )

    llmJson = json.loads(personalityResponse.choices[0].message.content)

    return llmJson


@api_view(["POST"])
def predictPersonality(request):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        # Cluster trait averages (from your dataset)
        clusterAverages = {
            "Ambitious & Charismatic Leaders": [2.95, 3.16, 3.06, 2.97, 3.10],
            "Creative but Emotionally Intense": [3.06, 2.36, 3.12, 3.09, 3.31],
            "Detail-Oriented & Cautious": [3.09, 3.72, 3.33, 3.37, 3.43],
            "Unstructured & Introverted": [0.44, 0.38, 0.41, 0.39, 0.36]
        }

         # Ensure the request body contains the userInput data
        if 'userInput' not in request.data:
            return HttpResponse('User input data is missing', status=500)

        # Example User Input
        userInput = request.data['userInput']

        # Generate and Print the Report
        personality = getModelPersonality(userInput)
        personalityJson = personalityInsights(clusterAverages, userInput, personality)
        print(personalityJson)

        return JsonResponse(personalityJson, safe=False)
         
    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)
    

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# ------------------------------ GENERATE QUESTIONS  -----------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
@api_view(["POST"])
def startInterview(request, fileId):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        fileObj = File.objects.filter(pk=fileId)

        if not fileObj.exists():
            return HttpResponse("File not found", status=404)
        
        else:

            file = fileObj.first()

            qnaPrompt = f"""
            Based on the following resume text, generate five interview questions that require specific and concrete answers, ensuring they can be compared with user responses. The questions should be based on projects, skills, technologies, roles and certifications mentioned in the resume. One out of the five question must be skill based that ismentioned in the resume.  Ensure no markdown, backticks, or additional text, the format should be as follows:
            {{
                "QUESTION1": {{ 
                    "question": "",
                    "answer": "Provide an in-depth and detailed response explaining the answer thoroughly with examples if necessary."
                }},
                "QUESTION2": {{ 
                    "question": "",
                    "answer": "Provide an in-depth and detailed response explaining the answer thoroughly with examples if necessary."
                }},
                "QUESTION3": {{ 
                    "question": "",
                    "answer": "Provide an in-depth and detailed response explaining the answer thoroughly with examples if necessary."
                }},
                "QUESTION4": {{ 
                    "question": "",
                    "answer": "Provide an in-depth and detailed response explaining the answer thoroughly with examples if necessary."
                }},
                "QUESTION5": {{ 
                    "question": "",
                    "answer": "Provide an in-depth and detailed response explaining the answer thoroughly with examples if necessary."
                }}
            }}

            Resume Text:
            {file.ocrText}
            """

            client = groq.Client(api_key=AIModelConfig.apiKey1)

            qnaResponse = client.chat.completions.create(
                model=AIModelConfig.qnaGenerationLLM,
                messages=[{"role": "system", "content": "You are an AI that generates job interview questions and detailed answers strictly without any extra formatting."},
                        {"role": "user", "content": qnaPrompt}],
                temperature=0.7,
                max_tokens=1500
            )

            qnaJson = json.loads(qnaResponse.choices[0].message.content)

            # Save to DB
            interview = InterviewSession.objects.create(userId=user, fileId=file, qnaJson=qnaJson)

            # Return only questions
            questions = {qid: {"question": data["question"]} for qid, data in qnaJson.items()}

            return JsonResponse({
                "interviewId": str(interview.id),
                "questions": questions
            })
        
    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def submitAudioResponse(request):
    try:
        interviewId = request.data.get("interviewId")
        questionId = request.data.get("questionId")
        audio_file = request.FILES.get("audio")

        if not all([interviewId, questionId, audio_file]):
            return HttpResponse("Missing fields", status=400)

        interview = InterviewSession.objects.filter(id=interviewId).first()
        if not interview:
            return HttpResponse("Interview session not found", status=404)

        qnaJson = interview.qnaJson

        if questionId not in qnaJson:
            return HttpResponse("Invalid question ID", status=400)

        # Transcribe
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_path = temp_audio.name

        client = groq.Client(api_key=AIModelConfig.apiKey3)
        response_text = ""
        with open(temp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_path), f.read()),
                model="distil-whisper-large-v3-en",
                response_format="verbose_json",
                prompt=("This is a professional job interview conversation. The content includes typical interview questions and responses. "
                                "Please maintain formal business language and accurate punctuation. "
                                "Transcribe clearly any mention of skills, qualifications, work experience, "
                                "and company-specific terminology. Format speaker transitions appropriately."),
                language="en",
                temperature=0.0
            )
            
            response_text = transcription.text if transcription else ""

        os.remove(temp_path)
        
        # Determine next step
        keys = list(qnaJson.keys())
        current_index = keys.index(questionId)

        # Update candidate response
        qnaJson[questionId]["candidateResponse"] = response_text
        interview.qnaJson = qnaJson
        interview.progress = current_index + 1
        interview.save()

        if current_index + 1 < len(keys):
            next_qid = keys[current_index + 1]
            next_question = qnaJson[next_qid]["question"]
            return JsonResponse({
                "transcript": response_text,
                "nextQuestionId": next_qid,
                "nextQuestion": next_question
            })
        else:
            return JsonResponse({
                "transcript": response_text,
                "interviewComplete": True
            })

    except Exception as e:
        return HttpResponse(str(e), status=500)

@api_view(["POST"])
def validateInterview(request):
    try:
        interviewId = request.data.get("interviewId")
        interview = InterviewSession.objects.filter(id=interviewId).first()
        if not interview:
            return HttpResponse("Invalid interview ID", status=404)

        qna = interview.qnaJson
        validated = responseValidator(qna)

        fileDirPath = Path(StaticData.objects.get(key="FilePath").value) / str(interview.userId.pk) / str(interview.fileId.pk) / str(interview.id)

        total_points, overallSummary = generate_PDF(validated, str(fileDirPath), getLoggedInUser(request).username)

        interview.reportStatus = "Generated"
        interview.score = total_points
        interview.summary = overallSummary
        interview.save()

        reportDetails = {
            "score": total_points,
            "summary": overallSummary,
            "reportPath": '/apiGetInterviewReport/'+str(interview.id),
        }

        return JsonResponse(reportDetails, safe=False)

    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)
    
@api_view(["GET"])
def getInterviewReport(request, interviewId):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        interview = InterviewSession.objects.filter(id=interviewId).first()
        if not interview:
            return HttpResponse("Interview session not found", status=404)

        if interview.userId.pk != user.pk:
            return HttpResponse("You are forbidden to access to this file", status=403)
        
        if interview.reportStatus != "Generated":
            return HttpResponse("Report not generated yet", status=400)

        reportPath = Path(StaticData.objects.get(key="FilePath").value) / str(interview.userId.pk) / str(interview.fileId.pk) / str(interview.id) / "Interview_Assessment.pdf"

        if not reportPath.exists():
            return HttpResponse("Report not found", status=404)

        with open(reportPath, 'rb') as pdf_file:
            # Read the file content into memory (bytes)
            data = pdf_file.read()

        # Create an in-memory image for the response
        fileBytes = BytesIO(data)

        return FileResponse(fileBytes, content_type="application/pdf")

    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# ---------------------------- COURSE RECOMMENDATIONS  ---------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# Create a function to extract the course data using Selenium and BeautifulSoup
def scrape_courses_selenium(extractURL):
    # Set up Selenium WebDriver (make sure you have the correct WebDriver installed, e.g., ChromeDriver)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(options=options)

    # Open the Coursera search page
    driver.get(extractURL)
    time.sleep(3)  # Wait for the page to load

    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract courses
    courses = []
    course_cards = soup.select('div[data-testid="product-card-cds"]')

    for card in course_cards:
        course = {}
        
        # Extract course name
        course_name = card.select_one('h3.cds-CommonCard-title')
        if course_name:
            course['course_name'] = course_name.text.strip()
        
        # Extract course link
        course_link = card.select_one('a[data-click-key="search.search.click.search_card"]')
        if course_link:
            course['course_link'] = 'https://www.coursera.org' + course_link['href']
        
        # Extract course image
        course_image = card.select_one('div.cds-CommonCard-previewImage img')
        if course_image:
            course['course_image'] = course_image['src']
        
        # Extract difficulty level
        difficulty = card.select_one('div.cds-CommonCard-metadata')
        if difficulty:
            course['difficulty'] = difficulty.text.strip()
        
        if course:
            courses.append(course)

    driver.quit()  # Close the WebDriver

    return courses
    
@api_view(["GET"])
def scrapeCourses(request, topic, level):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user        
        
        extractURL = f"https://www.coursera.org/search?query={topic}&productDifficultyLevel={level}"

        courses = scrape_courses_selenium(extractURL)

        print(courses)
        return JsonResponse(courses, safe=False)
         
    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)
    

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# ------------------------------ JOB RECOMMENDATIONS  ----------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
@api_view(["GET"])
def scrapeJobs(request, fileId, searchTerm, location):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        resumeInsightsObj = ResumeInsights.objects.filter(fileId=fileId)

        if not resumeInsightsObj.exists():
            return HttpResponse("Insights not found", status=404)
        
        resumeInsight = resumeInsightsObj.first()

        # User inputs from command line arguments
        # search_term = "AI Engineer"
        # location = "Bangalore"

        num_jobs = 6

        # Parse JSON fields from string to Python objects
        skills = resumeInsight.skills
        projects = resumeInsight.projects
        work_experience = resumeInsight.experience
        education = resumeInsight.education

        # Construct user_description
        user_description = ""

        if isinstance(skills, list):
            user_description += " ".join(skills)
        user_description += "\n"

        if isinstance(work_experience, list):
            for exp in work_experience:
                desc = exp.get("Description") or exp.get("description")
                if desc:
                    user_description += desc
        user_description += "\n"

        if isinstance(projects, list):
            for proj in projects:
                desc = proj.get("Description") or proj.get("description")
                if desc:
                    user_description += desc
        user_description += "\n"

        if isinstance(education, list):
            for edu in education:
                degree = edu.get("Degree") or edu.get("degree")
                if degree:
                    user_description += degree
        user_description += "\n"

        user_skills = skills

        # Initialize scraper and get data
        jobs_df = pd.DataFrame()

        scraper = NaukriJobScraper()
        print(f"\nStarting job scraper for '{searchTerm}' in {location}...")
        jobs_df = scraper.scrape_naukri_jobs(searchTerm, location, num_jobs)

        print(f"\nScraping complete. Found {len(jobs_df)} jobs.")
        
        # Check if we have job data
        if len(jobs_df) ==.0:
            print("No jobs were found. Please try again with different search terms.")
            return
        
        # Initialize recommender and get recommendations
        print("\nGenerating job recommendations based on your profile...")
        recommender = JobRecommender(jobs_df)
        recommendations = recommender.recommend_jobs(
            user_skills=user_skills,
            user_description=user_description,
            top_n=min(10, len(jobs_df))
        )
        
        jobRecommendationJson = recommendations.to_dict(orient="records")
        print(jobRecommendationJson)

        return JsonResponse(jobRecommendationJson, safe=False)
            
    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)
    

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# --------------------------- COVER LETTER GENERATION  ---------------------------
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
@api_view(["GET"])
def generateCoverLetter(request, fileId):
    try:
        # Authenticating User
        user = getLoggedInUser(request)
        
        if type(user) is not Login:
            return user
        
        fileObj = File.objects.filter(pk=fileId)

        if not fileObj.exists():
            return HttpResponse("File not found", status=404)
        
        else:

            file = fileObj.first()

            coverLetterPrompt = f"""
            You are an AI language model that assists candidates by generating professional cover letters.

            Based on the resume provided below, generate a formal and compelling cover letter tailored to a generic job application in the same domain as the resume. 

            The letter should be:
            - 3 to 4 paragraphs
            - Written in a professional tone
            - Highlight the candidate's key skills, experience, and enthusiasm
            - Suitable for submitting along with a resume for job applications

            Resume Text:
            {file.ocrText}
            """

            client = groq.Client(api_key=AIModelConfig.apiKey3)

            coverLetterResponse = client.chat.completions.create(
            model=AIModelConfig.LLM,
            messages=[
                {"role": "system", "content": "You are an AI that generates professional cover letters based on resume content."},
                {"role": "user", "content": coverLetterPrompt}
            ],
            temperature=0.7,
            max_tokens=2000
            )

            coverLetter = coverLetterResponse.choices[0].message.content.strip()
            print(coverLetter)

            return JsonResponse(coverLetter, safe=False)
        
    except Exception as e:
        print(e)
        return HttpResponse(str(e), status=500)