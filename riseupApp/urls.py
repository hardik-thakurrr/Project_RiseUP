from django.urls import path, re_path
from .views import *

# API routes
urlpatterns = [
    # Dynamic template rendering
    path('index/<str:page_name>/', dynamic_template_view, name='dynamic_template'),
    
    path('apiUpload', upload_file, name="upload_file"),

    path('apiRetryUpload/<int:fileId>', retryUpload, name="retry_upload"),
    
    path('apiSignup/', signup, name="signup"),

    path('apiLogin/', login, name="login"),
    
    path('login/', login_page, name="login_page"),
    
    path('apiGetUser/', getUserDetails, name="get_user_data"), 
    
    path('apiLogout/', logout, name="logout"), 
    
    path('apiDeleteFile/<int:fileId>', delete_file, name="delete_file"), 
    
    path('apiValidateFile/<int:fileId>', setValidatedStatus, name='validate_file'),
    
    path('apiFetchResumes/', searchFiles, name="fetch_resumes"),

    path('apiGetThumbnail/<int:fileId>', getThumbnailImage, name="get_thumbnail"),

    path('apiGetResumeInsights/<int:fileId>', getResumeInsights, name="resume_insights"),

    path('apiStartInterview/<int:fileId>', startInterview, name="start_interview"),

    path('apiSubmitAudioResponse', submitAudioResponse, name="submit_audio_response"),

    path('apiValidateInterview', validateInterview, name="validate_interview"),

    path('apiGetInterviewReport/<str:interviewId>', getInterviewReport, name="get_interview_report"),
    
    path('apiGetPersonalityInsights/', predictPersonality, name="personality_insights"),

    path('apiGetCourses/<str:topic>/<str:level>/', scrapeCourses, name="scrape_courses"),

    path('apiGetJobs/<int:fileId>/<str:searchTerm>/<str:location>/', scrapeJobs, name="scrape_jobs"),

    path('apiGetCoverLetter/<int:fileId>', generateCoverLetter, name="cover_letter"),
    
    path('apiGetCoverFile/<int:fileId>', getCoverFile, name="get_cover_file"),
    
    # Landing page (new index.html)
    path('', landing_page, name='landing_page'),

    # Catch-all for other frontend routes
    re_path(r'^(?!login\/?)(?!media).*$', index_page),
]