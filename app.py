import os
import re
import PyPDF2 as pdf
from io import BytesIO
import streamlit as st 
from docx import Document 
from dotenv import load_dotenv 
from reportlab.pdfgen import canvas 
import google.generativeai as genai 
from reportlab.lib.pagesizes import A4 


# Load environment variables
load_dotenv()

# Configure generative AI
model = genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt):
    """Extract keywords from job description using Gemini."""
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_prompt)
    return response.text


def extract_text_from_pdf(file):
    """Extract text from PDF file."""
    try:
        reader = pdf.PdfReader(file)
        text = ' '.join([str(page.extract_text()) for page in reader.pages])
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None


def extract_text_from_docx(docx_file):
    """Extract text from DOCX file."""
    try:
        doc = Document(docx_file)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text from DOCX file: {e}")
        return ""
    
def extract_text(file):
    """Extract text from supported file types (PDF, DOCX)."""
    supported_formats = (".pdf", ".docx")
    if not file.name.lower().endswith(supported_formats):
        st.error(f"Error: Unsupported file type. Supported formats: {', '.join(supported_formats)}")
        return None
    
    if file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(file)
    else:  # Assume .docx
        return extract_text_from_docx(file)


def generate_formatted_resume(new_resume):
    """Generate a formatted PDF resume."""
    if new_resume is None:
        st.error("Error: Cannot generate formatted resume. Input is empty.")
        return None

    # Create a PDF document
    text_resume = re.sub(r'[*_`~]', '', new_resume)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Set up formatting options
    c.setFont("Helvetica", 12)
    margin = 15
    line_height = 13

    # Split the text into lines
    lines = text_resume.split('\n')
    y_position = 600

    # Write the lines to the PDF
    for line in lines:
        c.drawString(margin, y_position, line)
        y_position -= line_height
        if y_position < margin:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = 800

    # Save the PDF
    c.save()
    return buffer



def analyze_resume(job_description, uploaded_file):
    """Analyze resume based on job description and uploaded file."""
    if not uploaded_file:
        st.error("Error: Uploaded file not found.")
        return None

    text_resume = extract_text(uploaded_file)
    if not text_resume:
        return None
    
    prompt_1 = """ 
        Input Tasks:
        You have been assigned to evaluate a candidate's resume using generative AI to assess alignment with a job description. Here's the breakdown of your tasks:

        1. Review the provided resume against the job description.
        2. Share a professional evaluation on whether the candidate's profile aligns with the role.
        3. Extract and highlight essential skills and requirements from the job description.
        4. Focus on keywords representing core responsibilities, qualifications, must-have, and desirable skills.
        5. Analyze the resume content and compare it to the extracted keywords.
        6. Calculate a percentage matching score indicating how well the applicant's skills align with the job requirements.

        Output Task:
        Please demonstrate professionalism and creativity in your findings.

        Candidate Matching Score: percentage_match 0-100%
        - Job Title: 
        - Resume Analysis: 

        Highlighted Keywords Table:
        Organize extracted keywords from the job description and compare them with the resume in a table with columns:
        | Category          | Job Keyword   | Missing Keyword | Resume Keyword | Percentage Match |
        |-------------------|---------------|-----------------|----------------|------------------|
        | Responsibilities  | keyword       | Missing Keyword | Resume Keyword | percentage_match |
        | Qualifications    | keyword       | Missing Keyword | Resume Keyword | percentage_match |
        | Must-Have Skills  | keyword       | Missing Keyword | Resume Keyword | percentage_match |
        | Desirable Skills  | keyword       | Missing Keyword | Resume Keyword | percentage_match |
        | Top Skills        | keyword       | Missing Keyword | Resume Keyword | percentage_match |

        Missing Keywords:
        Identify missing keywords from the job description:
        - Missing Keyword 1
        - Missing Keyword 2
        - Missing Keyword 3

        Educational Links:
        For each missing keyword, provide relevant educational resources (websites or online courses) to help the candidate develop that skill:
        Missing Keyword: Python Programming
        - Resource 1: Link
        - Resource 2: Link
        - Resource 3: Link

        Suggestions for Optimization:
        Provide clear and precise suggestions for the candidate to optimize their resume to better match the job description and improve their chances of securing an interview.

        Notes:
        - Focus on identifying impactful keywords reflecting core responsibilities, qualifications, and must-have/desirable skills.
        - Ensure accuracy in detecting missing keywords for comprehensive feedback.
        - Format the table clearly and precisely for accurate presentation.

        
    """
    keywords_response = get_gemini_response(prompt_1 + str((text_resume, job_description)))
    return keywords_response


def generate_resume(job_description, text_resume, keywords_response):
    """Generate a new resume based on job description, text resume, and keywords response."""
    text_resume_cleaned = re.sub(r'[*_`~]', '', text_resume)

    prompt_input = """
        Input:
        Task:
        Optimize the candidate's job experiences by incorporating specific missing keywords {keywords_response} from the job description to enhance competitiveness. Modify each job experience using the following keywords to align with the job requirements.

        Instructions:
        - Review Job Description: Study the provided job description thoroughly to identify key skills, responsibilities, and qualifications required for the role.
        - Analyze Candidate's Resume: Evaluate the candidate's job experiences listed in their resume.
        - Modify Job Experiences: Enhance each job role listed on the resume by incorporating relevant missing keywords {keywords_response} extracted from the job description.
        - Integrate relevant keywords related to core responsibilities, qualifications, must-have skills, and desirable skills into each job description.
        - Ensure that the revised job experiences demonstrate a strong match with the job requirements.
        - Ensure Keyword Relevance: Integrate keywords naturally into the job descriptions to demonstrate a strong match between the candidate's skills and the job requirements.
        - Enhance Competitiveness: Emphasize the candidate's experiences using language that resonates with the job description.
        - Use bullet points: Limit to a maximum of 4 bullet points per past experience.
        
        - Ensure to use the [Resume Format] to generate the new resume
    """

    prompt_output = """
        Output:
        Missing Keywords:Identify missing keywords from the job description:
        - Missing Keyword 1
        - Missing Keyword 2
        - Missing Keyword 3
            
        - Provide revised job experience descriptions for each role on the candidate's resume, enriched with appropriate keywords from the job description to enhance competitiveness.
        - Ensure a maximum of 4 bullet points in the experience to optimize readability and impact.
      Note:
           - Ensure creativity, precise, 
           - Ensure to use the [Resume Format] to generate the new resume
        
            Resume Format:
                - Contact Information:
                - Education:
                
                - Key Strengths:
                    • use missing keywords to generate sentences
                    •
                    •
                
                - Skills:
                    •
                    •
                    •
                
                - Experience:
                Position | Company | Date:
                    • use missing keywords to generate sentences
                    •
                    •
                    • 
                Position | Company | Date:
                    • use missing keywords to generate sentences
                    •
                    •
                    • 
                Position | Company | Date:
                    • use missing keywords to generate sentences
                    •
                    •
                    • 
    """
    new_resume = get_gemini_response(prompt_input + str((job_description, keywords_response, text_resume_cleaned)))

    if new_resume is not None:
        # Finalize the resume format with the generated content
        formatted_resume = get_gemini_response(prompt_output + str((new_resume, text_resume_cleaned)))
        if formatted_resume:
            return formatted_resume  # Return the formatted new resume content
        else:
            st.error("Error: Failed to generate a formatted resume.")
           
    else:
        st.error("Error: Failed to generate a new resume based on provided input.")
    return new_resume


def main():
    
    """Main function to run the application."""
    st.set_page_config(page_title="SmartAPP", page_icon=":book:")
    st.title("Smart ATS")
    st.text("Improve Your Resume ATS")

    job_description = st.sidebar.text_area("Paste the Job Description")
    uploaded_file = st.sidebar.file_uploader("Upload Resume", type=("pdf", "docx"))

    submit = st.sidebar.button("ATS Scan")
    resume_button = st.sidebar.button("Generate Resume")

    if submit:
        if uploaded_file:
            keywords = analyze_resume(job_description, uploaded_file)
            if keywords:
                st.write("Keywords:", keywords)
            else:
                st.error("Error: Failed to generate keywords.")

    if resume_button:
        if uploaded_file:
            text_resume = extract_text(uploaded_file)
            if text_resume:
                keywords = analyze_resume(job_description, uploaded_file)
                if keywords:
                    new_resume = generate_resume(
                        job_description, text_resume, keywords
                    )
                    st.write("New Generated Resume:")
                    st.write(new_resume)
                    formatted_filename = generate_formatted_resume(new_resume)
                    st.download_button("Download Formatted Resume as PDF", formatted_filename, "formatted_resume.pdf", "application/pdf")
                else:
                    st.error("Error: Failed to generate keywords.")
        else:
            st.error("Error: Unable to generate resume. Uploaded file not found.")

if __name__ == "__main__":
    main()
