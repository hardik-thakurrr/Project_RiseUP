from django.apps import AppConfig
from django.conf import settings
import joblib
import torch
import transformers
from torch import cuda
device='cuda' if cuda.is_available() else 'cpu'
from transformers import BertTokenizer

from ultralytics import YOLO

# from nltk.corpus import stopwords
# from nltk.stem import WordNetLemmatizer
# nltk.download(['stopwords','wordnet'])

# nltk.download('punkt_tab')
# nltk.download('averaged_perceptron_tagger_eng')

class RiseupappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'riseupApp'

class BERTClass(torch.nn.Module):
    def __init__(self):
        super(BERTClass, self).__init__()
        self.l1 = transformers.BertModel.from_pretrained('bert-base-uncased')
        self.l2 = torch.nn.Dropout(0.3)
        self.l3 = torch.nn.Linear(768, 24)

    def forward(self, ids, mask, token_type_ids):
        _, output_1= self.l1(ids, attention_mask = mask, token_type_ids = token_type_ids, return_dict=False)
        output_2 = self.l2(output_1)
        output = self.l3(output_2)
        return output

class AIModelConfig(AppConfig):
    name = 'AIModelConfig'
    BASE_MODEL_PATH = settings.MODELS

    # +-+-+-+-+-+-+-+-+-+- YOLO MODEL +-+-+-+-+-+-+-+-+-+-
    yoloModelPath = BASE_MODEL_PATH.joinpath('Yolo','yolov11m-doclaynet.pt')
    yoloModel = YOLO(yoloModelPath)
    print(f"YOLO Model Loaded Successfully !!")

    # +-+-+-+-+-+-+-+-+-+- DOMAIN MODEL +-+-+-+-+-+-+-+-+-+-
    MAX_LEN = 512
    domainModelPath = BASE_MODEL_PATH.joinpath('Domain','model.pth')

    domainTokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    
    domainModel = BERTClass()
    domainModel.load_state_dict(torch.load(domainModelPath, map_location=torch.device('cuda' if torch.cuda.is_available() else 'cpu')))
    domainModel.to(device)
    domainModel.eval()  

    categories = ["ACCOUNTANT", "ADVOCATE", "AGRICULTURE", "APPAREL", "ARTS", "AUTOMOBILE", "AVIATION", "BANKING", "BPO", "BUSINESS-DEVELOPMENT", "CHEF", "CONSTRUCTION", "CONSULTANT", "DESIGNER", "DIGITAL-MEDIA", "ENGINEERING", "FINANCE", "FITNESS", "HEALTHCARE", "HR", "INFORMATION-TECHNOLOGY", "PUBLIC-RELATIONS", "SALES", "TEACHER"]

    print(f"Domain Model Loaded Successfully !!")

    # +-+-+-+-+-+-+-+-+-+- PERSONALITY MODEL +-+-+-+-+-+-+-+-+-+-

    personalityModelPath = BASE_MODEL_PATH.joinpath('Personality','model.pkl')
    personalityScalerPath = BASE_MODEL_PATH.joinpath('Personality','scaler.pkl')
    personalityEncoderPath = BASE_MODEL_PATH.joinpath('Personality','encoder.pkl')

    # Load trained model, scaler, and label encoder
    personalityModel = joblib.load(personalityModelPath)
    personalityScaler = joblib.load(personalityScalerPath)
    personalityEncoder = joblib.load(personalityEncoderPath)

    print(f"Personality Model Loaded Successfully !!")

    # +-+-+-+-+-+-+-+-+-+- API KEY +-+-+-+-+-+-+-+-+-+-
    apiKey1 = "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"
    apiKey2 = "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"
    apiKey3 = "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"

    
    # +-+-+-+-+-+-+-+-+-+- LLM MODELS +-+-+-+-+-+-+-+-+-+-

    LLM = "llama-3.3-70b-versatile"

    qnaGenerationLLM = "mistral-saba-24b"

    interviewLLM1 = ""

    interviewLLM2 = ""

