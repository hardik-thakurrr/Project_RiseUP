from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

apikey="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"


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=apikey,
    
)

llm2 = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=apikey,
    
)

interview_assessment_prompt = """
You are an AI-powered interview assessment tool. Your purpose is to evaluate candidate responses to interview questions by first establishing the scoring rubric and marks, then providing scores and constructive feedback based on this rubric.

Your responsibilities:

1. **Establish the Scoring Rubric:** Carefully analyze the specific details and context of the ideal answer ({ideal_Answer}). Create a detailed, four-level scoring rubric (1, 2, 3, 4 points).
2. **Make the Rubric Specific:** Ensure that the rubric is tailored to the project or subject matter described in the ideal answer. Avoid generic criteria — focus on the specific skills, methods, and outcomes mentioned.
3. **Output only the Scoring Rubric:** Provide only the detailed breakdown of scoring criteria and point values nothing else.
4. **Strictly Follow the Example Format:** Use the example provided to structure your output. Be clear, concise, and consistent in your rubric creation.

Input Format:

- **Question:** {question}
- **Ideal Answer:** {ideal_Answer}

Scoring Rubric Structure:

-4 points (Excellent): Fully captures the specific technical methods, key elements, and real-world impact described in the ideal answer, providing detailed and well-articulated examples.
-3 points (Good): Addresses the key aspects of the ideal answer, mentioning technical methods and real-world impact, but lacks depth or clarity in some areas.
-2 point (Fair): References some aspects of the ideal answer but provides limited or unclear information about the technical approach and real-world impact.
-1 points (Poor): Fails to align with the ideal answer, lacking key technical details, real-world impact, or clear understanding of the project’s significance.

For your convenience, here is a sample output for a scoring rubric:
4 points:
Mentions the specific technical skills learned (web development, HTML, CSS, Bootstrap, APIs, JavaScript, Angular JS and TS, NodeJS, and Git).
Provides detailed descriptions of technical methods used (taking online courses, reading documentation, practicing through hands-on projects).
Clearly articulates the benefits of seeking help from mentors and team members (learning from their perspectives, finding more efficient solutions).
Demonstrates a clear understanding of the real-world impact of learning these skills (ability to learn new technical skills quickly and efficiently for a project or role).

3 points:
Mentions the specific technical skills learned (web development, HTML, CSS, Bootstrap, APIs, JavaScript, Angular JS and TS, NodeJS, and Git).
References technical methods used (taking online courses, reading documentation, practicing through hands-on projects).
Briefly mentions seeking help from mentors and team members.
Touches on the real-world impact of learning these skills.

2 points:
References some of the specific technical skills learned (web development, HTML, CSS, Bootstrap, APIs, JavaScript, Angular JS and TS, NodeJS, and Git).
Mentions some technical methods used (taking online courses, reading documentation).
Provides limited information about seeking help from mentors and team members.
Lacks clear understanding of the real-world impact of learning these skills.

1 point:
Fails to mention specific technical skills learned.
Lacks clear understanding of technical methods used.
Does not mention seeking help from mentors and team members.
Lacks any clear understanding of the real-world impact of learning these skills."""



assessment_prompt=  """
You will receive input in the following format:
Candidate Response to The question: {answer}
Scoring Rubric:{Rubric}

Output Format:
Your output should be structured as follows:
Score: [The numerical score assigned to the response based STRICTLY on the scoring rubric, ranging from 1 to 4 points.  The score MUST be justified by direct evidence from the Candidate Response. Do not be influenced by subjective terms or positive/negative sentiment in the Candidate Response.]
Strengths: [2-3 lines highlighting the positive aspects of the candidate's response, specifically referencing elements from the response and how they align with the rubric. IF NO STRENGTHS ARE PRESENT ACCORDING TO THE RUBRIC, THEN WRITE "NONE"]
Areas for Improvement: [2-3 lines suggesting specific ways the candidate could improve their response in the future, providing actionable advice and linking it to elements missing from the rubric.]
"""
# assessment_prompt=  """

# I will give the Candidate Response and Scoring Rubric. You will provide the Score, Strengths, and Areas for Improvement based on the rubric.

# YOUR JOB IS TO MAKE SURE THAT ANSWER GIVEN: {answer}
# IS CLOSE TO: {Rubric} AND GIVE SCORE, STRENGTHS, AND AREAS FOR IMPROVEMENT

# You will receive input in the following format:
# Candidate Response: {answer}
# Scoring Rubric: {Rubric}

# **Output Format:**

# Your output should be structured as follows:

# Score: [The numerical score assigned to the response based on the scoring rubric.]

# Strengths: [2-3 LINE points highlighting the positive aspects of the candidate's response. Be specific and reference elements from the response.IF NO STRENGTHS THEN WRITE NONE]

# Areas for Improvement: [2-3 LINE points suggesting specific ways the candidate could improve their response in the future. Provide actionable advice.]

# AN EXAMPLE FOR YOUR UNDERSTANDING:
# Score: 2 points
# Strengths:
# Mentions the specific technical skills learned (web development, HTML, CSS, Bootstrap, APIs, JavaScript, Angular JS and TS, NodeJS, and Git).
# References technical methods used (taking online courses, reading documentation, practicing through hands-on projects).
# Areas for Improvement:
# Could provide more detail on the real-world impact of learning these skills.

# **Instructions:**

# You are to apply this framework to evaluate candidate responses to interview questions. Remember to stay objective, provide helpful feedback, and adhere to the specified input and output formats. Now begin!
# no asteriks or anything else only  in points FORMAT
# """


summary_prompt = """
You are an AI-powered interview assessment tool designed to evaluate candidate responses to interview questions. Your role is to provide a detailed assessment, including an overall summary based on the individual evaluations already completed.

For each question, evaluations have been conducted and scores assigned.

    Questions: {questions}
    Answers: {answers}
    Rubrics: {rubrics}
    Scores: {scores}
    Improvements: {improvements}

Your task now is to:
1. Review the individual scores and feedback provided
2. Provide a balanced and insightful overview of the candidate’s readiness.do this step once u have reviewed all the questions and their scores and feedback
3. The output should be 100 words that give me a summary of the candidate's performance in the interview.Not each question but the overall performance.
4. Do not add any extra Information.Direct Summary.


Ensure the overall summary is clear, actionable, and designed to reflect both the candidate's strong points and opportunities for growth.

Example on how the output MUST BE:
The candidate's performance in the interview suggests a need for improvement in understanding fundamental concepts in machine learning. Out of four questions, the candidate scored 0 points on supervised learning, 1 point on unsupervised learning, and 0 points on confusion matrix and feature engineering. The feedback highlights a lack of clarity and relevance in their responses, indicating a need for more in-depth knowledge and practice in these areas.
"""


def responseValidator(interview_questions_json):

    for key, item in interview_questions_json.items():
        question = item['question']
        ideal_Answer = item.get('answer')

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", interview_assessment_prompt)]
        )

        chain = prompt_template | llm | StrOutputParser()

        rubrics = chain.invoke({"question": question, "ideal_Answer": ideal_Answer})

        item['Rubric'] = rubrics  # Add the rubric directly to the JSON structure
        
    print("working on Eval")

    for key, item in interview_questions_json.items():
        question = item['question']
        answer = item.get('candidateResponse')
        rubric = item.get('Rubric')

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", assessment_prompt)]
        )

        chain = prompt_template | llm2 | StrOutputParser()

        response = chain.invoke({"answer": answer, "Rubric": rubric})

        print(response)

        # Extract Score, Strengths, and Areas for Improvement from response
        # item['Score'] = response.split('• Score:')[1].split('\n')[0].strip()
        # item['Strengths'] = response.split('• Strengths:')[1].split('• Areas for Improvement:')[0].strip()
        # item['AreasForImprovement'] = response.split('• Areas for Improvement:')[1].strip()

        item['Score'] = response.split('Score:')[1].split('\n')[0].strip()
        item['Strengths'] = response.split('Strengths:')[1].split('Areas for Improvement:')[0].strip()
        item['AreasForImprovement'] = response.split('Areas for Improvement:')[1].strip()
    
    return interview_questions_json


def CandidateSummary(df):
    all_questions = []
    all_answers = []
    all_rubrics = []
    all_scores = []
    all_strengths = []
    all_improvements = []

    for index, row in df.iterrows():
        all_questions.append(row['question'])
        all_answers.append(row['candidateResponse'])
        all_rubrics.append(row['Rubric'])
        all_scores.append(row['Score'])
        # all_strengths.append(row['Strength'])
        all_improvements.append(row['AreasForImprovement'])

    # combined_data = {
    #     "questions": "; ".join(all_questions),
    #     "answers": "; ".join(all_answers),
    #     "rubrics": "; ".join(all_rubrics),
    #     "scores": "; ".join(map(str, all_scores)),
    #     # "strengths": "; ".join(all_strengths),
    #     "improvements": "; ".join(all_improvements)
    # }

    questions = "; ".join(all_questions)
    answers = "; ".join(all_answers)
    rubrics = "; ".join(all_rubrics)
    scores = "; ".join(map(str, all_scores))
    # strengths = "; ".join(all_strengths)
    improvements = "; ".join(all_improvements)

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", summary_prompt)]
    )

    chain = prompt_template | llm2 | StrOutputParser()

    response = chain.invoke({
        "questions": questions,
        "answers": answers,
        "rubrics": rubrics,
        "scores": scores,
        # "strengths": strengths,
        "improvements": improvements
    })
    print(response)
    return response
