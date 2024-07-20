import os
import google.generativeai as genai
import streamlit as st
import pandas as pd

from PyPDF2 import PdfReader
from io import BytesIO
import time

def calculate_score(list1, list2):
    point = 0
    if len(list1) != len(list2):
        raise ValueError("Both lists must be of the same length")

    for i in range(0,len(list1)):

        if list1[i]==list2[i]:
            point = point+1

    return point

def text_to_questions(text, key):
    os.environ["GOOGLE_API_KEY"] = key

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    Please create 10 multiple-choice questions (MCQs) in the following format:
        Topic = {text}
        Format:

        <START>("Question", ["A)Option1", "B)Option2", "C)Option3", "D)Option4"], "D", "DifficultyLevel")<END>

        Requirements:

        4 questions should be hard.
        2 questions should be easy.
        4 questions should be medium.
        Do not include questions with quotes or citations.
        Example:
        <question1>
        <START>("What is the capital of France?", ["A)Paris", "B)London", "C)Berlin", "D)Madrid"], "A", "easy")<END>
        <question2>
        <START>("What is the capital of India?", ["A)Paris", "B)London", "C)Delhi", "D)Madrid"], "C", "easy")<END>
        ....
        Outcome:
       Only provide the questions in the specified format.
       Each question should be a string, options will be inside one list,
       the correct answer will be a string, and the difficulty level will be in
       the form of a string all of above inside one tuple.Each question will be one line.
       Ensure the format is correct and provide
       no additional information.
     """
    response = model.generate_content(prompt)
    return response.text


def question_csv():
    data = []
    with open('artifacts/output.txt', 'r', encoding='utf-8') as file:
        for line in file:
            text = line.strip()
            if text[0:7] == "<START>" and text[-5:] == "<END>":
                text = text.replace("<START>", "")
                text = text.replace("<END>", "")
                text = eval(text)
                data.append(text)

    question_list = []
    option_list = []
    ans_list = []
    diff_list = []
    for i in data:
        question_list.append(i[0])
        option_list.append(i[1])
        ans_list.append(i[2])
        diff_list.append(i[3])
    data = {"question": question_list, "options": option_list, "answer": ans_list, "difficulty": diff_list}

    df = pd.DataFrame(data)
    df.to_csv("artifacts/data.csv")
    return df


st.title('PDF Question and Answer')
key = st.text_input('Enter KEY:')
gender = st.radio('Gender:', ['Male', 'Female'])
edu_lang = st.radio('Educational Language:', ['English', ' Non-English'])
age = st.slider('AGE', min_value=10, max_value=110)

st.subheader('Input PDF path')
uploaded_file = st.file_uploader('PDF File uploader', type='pdf')

data = []
if uploaded_file is not None:
    pdf_reader = PdfReader(BytesIO(uploaded_file.read()))
    num_pages = len(pdf_reader.pages)
    st.write(f'The PDF file has {num_pages} pages.')

    start_page = st.number_input('Enter start page number', min_value=1, max_value=num_pages, step=1)
    end_page = st.number_input('Enter end page number', min_value=start_page, max_value=num_pages, step=1)

    if st.button('Show Page Content + Create question'):
        pdf_text = ""
        for page_num in range(start_page - 1, end_page):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            pdf_text += page_text + "\n"
        data.append(pdf_text)
        st.text_area(f'Content from page {start_page} to {end_page}', pdf_text, height=300)
else:
    st.write("Please upload a PDF file to display its content.")


with st.form(key='survey_form'):
    qu = text_to_questions(text=data, key=key)
    with open('artifacts/output.txt', 'w', encoding='utf-8') as file:
        file.write(f"{qu}")
    df = question_csv()

    val = []
    count = 0
    for index, row in df.iterrows():
        ques = row['question']
        opt = row['options']
        st.write(f'{ques}')
        st.write(f'{opt}')
        selected_option = st.radio('Pick one:', ['A', 'B', 'C', 'D'], horizontal=True, index=None, key=f"{count}")
        val.append(selected_option)
        count += 1

    submit_button = st.form_submit_button(label='Submit')
    if submit_button:

        correctans = []
        for ans in df["answer"]:
            correctans.append(ans)
      
        point = calculate_score(val,correctans)
        st.write('Point is :', point)
