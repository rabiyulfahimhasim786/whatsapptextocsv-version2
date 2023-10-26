from django.urls import path

from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path('resumeupload/', views.upload_and_extract_resume, name='resumeupload'),
    path('success/', views.success_view, name='success_view'),
    path('extracted_resumes/', views.extracted_resume_list, name='extracted_resumes'),
    path('extracted_resumes/edit/<int:pk>', views.edit_extracted_resume, name='edit_extracted_resume'),
    path('extracted_resumes/delete/<int:pk>', views.delete_extracted_resume, name='delete_extracted_resume'),

    path('extracted_resumes/profile/<int:pk>', views.update_profile, name='profile'),
    path('extracted_resumes/objective/<int:pk>', views.update_objective, name='objective'),
    path('extracted_resumes/professional/<int:pk>', views.update_professional, name='professional'),
    path('extracted_resumes/education/<int:pk>', views.update_education, name='education'),
    path('extracted_resumes/skill/<int:pk>', views.update_skill, name='skill'),
    path('extracted_resumes/experience/<int:pk>', views.update_experience, name='experience'),
    path('extracted_resumes/reference/<int:pk>', views.update_reference, name='reference'),
    path('extracted_resumes/certificate/<int:pk>', views.update_certificate, name='certificate'),
    path('extracted_resumes/award/<int:pk>', views.update_award, name='award'),
    path('extracted_resumes/hobbies/<int:pk>', views.update_hobbies, name='hobbies'),

    path('extracted_resumes/addexperience/<int:pk>', views.add_candidate_experience, name='add_candidate_experience'),
    path('extracted_resumes/add/<int:pk>', views.add, name='add'),
    path('extracted_resumes/addeducation/<int:pk>', views.add_education, name='addeducation'),
    path('extracted_resumes/addreference/<int:pk>', views.add_reference, name='addreference'),
    path('extracted_resumes/addcertificate/<int:pk>', views.add_certificate, name='addcertificate'),
    path('extracted_resumes/addaward/<int:pk>', views.add_award, name='addaward'),
    path('extracted_resumes/addhobbies/<int:pk>', views.add_hobbies, name='addhobbies'),

    path('extracted_resumes/skillsdelete/<int:pk>', views.delete_skills_resume, name='delete_skills_resume'),
    path('extracted_resumes/educationdelete/<int:pk>', views.delete_education_resume, name='delete_education_resume'),
    path('extracted_resumes/experiencedelete/<int:pk>', views.delete_experience_resume, name='delete_experience_resume'),
    path('extracted_resumes/referencedelete/<int:pk>', views.delete_reference_resume, name='delete_reference_resume'),
    path('extracted_resumes/certificatedelete/<int:pk>', views.delete_certificate_resume, name='delete_certificate_resume'),
    path('extracted_resumes/awarddelete/<int:pk>', views.delete_award_resume, name='delete_award_resume'),
    path('extracted_resumes/hobbiesdelete/<int:pk>', views.delete_hobbies_resume, name='delete_hobbies_resume'),

    path('extracted_resumes/editskills/<int:pk>', views.edit_candidateskill, name='edit_candidateskill'),
    path('extracted_resumes/get_edit_screen_skills_experience', views.get_edit_screen_skills_experience, name='get_edit_screen_skills_experience'),
    path('extracted_resumes/edit_skills_experience/<int:pk>', views.edit_skills_experience, name='edit_skills_experience'),
    path('extracted_resumes/get_edit_screen_education', views.get_edit_screen_education, name='get_edit_screen_education'),
    path('extracted_resumes/edit_education/<int:pk>', views.edit_education, name='edit_education'),
    path('extracted_resumes/get_edit_screen__by_email', views.get_edit_screen__by_email, name='get_edit_screen__by_email'),
    path('extracted_resumes/edit_by_email/<int:pk>', views.edit_by_email, name='edit_by_email'),
    path('extracted_resumes/get_edit_screen_experience', views.get_edit_screen_experience, name='get_edit_screen_experience'),
    path('extracted_resumes/edit_experience/<int:pk>', views.edit_experience, name='edit_experience'),

    path('extracted_resumes/get_edit_screen_certificate', views.get_edit_screen_certificate, name='get_edit_screen_certificate'),
    path('extracted_resumes/edit_certificate_code/<int:pk>', views.edit_certificate_code, name='edit_certificate_code'),

    path('extracted_resumes/get_edit_screen_award', views.get_edit_screen_award, name='get_edit_screen_award'),
    path('extracted_resumes/edit_award/<int:pk>', views.edit_award, name='edit_award'),

    path('extracted_resumes/get_edit_screen_hobbies', views.get_edit_screen_hobbies, name='get_edit_screen_hobbies'),
    path('extracted_resumes/edit_hobbies/<int:pk>', views.edit_hobbies, name='edit_hobbies'),

    path('extracted_resumes/get_edit_screen_job_skills', views.get_edit_screen_job_skills, name='get_edit_screen_job_skills'),
    path('extracted_resumes/edit_skills_used/<int:pk>', views.edit_skills_used, name='edit_skills_used'),
    path('extracted_resumes/update_or_create/<int:pk>', views.edit_by_candidatereparser, name='update_or_create'),
]

