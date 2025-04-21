import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
# nltk.download(['stopwords','wordnet'])

# nltk.download('punkt_tab')
# nltk.download('averaged_perceptron_tagger_eng')

import torch
from torch import cuda
device='cuda' if cuda.is_available() else 'cpu'

def clean_resume(resume_str, common_words=['state', 'company', 'city', 'name']):

    # Converting to Lowercase
    resume_str = resume_str.lower()

    # Remove extra whitespaces and newline characters
    cleaned_text = re.sub('\s+', ' ', resume_str).strip()

    # Replacing forward slashes
    cleaned_text = re.sub(r'\/', ' ', cleaned_text)

    # Remove URLs
    cleaned_text = re.sub(r'http\S+|www\S+|https\S+', '', cleaned_text, flags=re.MULTILINE)

    # Remove @ mentions
    cleaned_text = re.sub(r'@\S+', '', cleaned_text)

    # Remove hashtags
    cleaned_text = re.sub(r'#\S+', '', cleaned_text)

    # Remove RT (retweets) and CC (carbon copies)
    cleaned_text = re.sub(r'\bRT\b|\bCC\b', '', cleaned_text)

    # Remove non-alphanumeric characters and special characters except spaces
    cleaned_text = re.sub('[^A-Za-z0-9\s]', '', cleaned_text)

    # Remove multiple consecutive spaces
    cleaned_text = re.sub(' +', ' ', cleaned_text)

    # Removal of Stopwords and Common Words
    txt = nltk.tokenize.word_tokenize(cleaned_text)
    english_stopwords = set(stopwords.words('english'))
    if common_words is not None:
        english_stopwords.update(common_words)
    words = [w for w in txt if not w in english_stopwords]

    # POS Tagging
    tagged_words = nltk.pos_tag(words)
    filtered_words = [word for word, tag in tagged_words if tag not in ['DT', 'IN', 'TO', 'PRP', 'WP']]

    # Lemmatization
    lm = WordNetLemmatizer()
    cleaned_words = [lm.lemmatize(word) for word in filtered_words]

    return ' '.join(cleaned_words)
    
# Define a function to predict the category of a resume text
def predict_category(resume_text, model, tokenizer, max_len):

    resume_text = clean_resume(resume_text)

    # Tokenize the input text
    inputs = tokenizer.encode_plus(
        resume_text,
        None,
        add_special_tokens=True,
        max_length=max_len,
        padding='max_length',
        return_token_type_ids=True,
        return_attention_mask=True,
        truncation=True
    )

    # Convert tokenized text into tensors
    input_ids = torch.tensor(inputs['input_ids']).unsqueeze(0)  # Add batch dimension
    attention_mask = torch.tensor(inputs['attention_mask']).unsqueeze(0)  # Add batch dimension
    token_type_ids = torch.tensor(inputs["token_type_ids"]).unsqueeze(0)  # Add batch dimension

    # Move tensors to GPU if available
    if torch.cuda.is_available():
        input_ids = input_ids.to('cuda')
        attention_mask = attention_mask.to('cuda')
        token_type_ids = token_type_ids.to('cuda')

    # Pass input tensors through the model to get predictions
    with torch.no_grad():
        outputs = model(input_ids, attention_mask, token_type_ids)

    # Convert logits to probabilities using softmax
    probabilities = torch.softmax(outputs, dim=1)

    # Get the predicted category label
    predicted_category_index = torch.argmax(probabilities, dim=1).item()

    # Return the predicted category label
    return predicted_category_index