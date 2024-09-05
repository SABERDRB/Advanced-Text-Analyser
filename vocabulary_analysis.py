import re
import math
from collections import Counter
import random
from openai import OpenAI
import os

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def tokenize_text(text):
    return re.findall(r'\b\w+\b', text.lower())

def sentence_tokenize(text):
    return re.split(r'(?<=[.!?])\s+', text)

def calculate_flesch_kincaid_grade(text):
    sentences = len(sentence_tokenize(text))
    words = len(tokenize_text(text))
    syllables = sum(count_syllables(word) for word in tokenize_text(text))
    
    if sentences == 0 or words == 0:
        return 0
    
    grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    return round(grade, 1)

def calculate_flesch_reading_ease(text):
    sentences = len(sentence_tokenize(text))
    words = len(tokenize_text(text))
    syllables = sum(count_syllables(word) for word in tokenize_text(text))
    
    if sentences == 0 or words == 0:
        return 0
    
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return round(score, 1)

def calculate_gunning_fog_index(text):
    sentences = len(sentence_tokenize(text))
    words = tokenize_text(text)
    complex_words = [word for word in words if count_syllables(word) > 2]
    
    if sentences == 0 or len(words) == 0:
        return 0
    
    index = 0.4 * ((len(words) / sentences) + 100 * (len(complex_words) / len(words)))
    return round(index, 1)

def calculate_smog_index(text):
    sentences = sentence_tokenize(text)
    polysyllables = [word for word in tokenize_text(text) if count_syllables(word) >= 3]
    
    if len(sentences) < 30:
        return 0  # SMOG is reliable only for 30+ sentences
    
    index = 1.0430 * math.sqrt(len(polysyllables) * (30 / len(sentences))) + 3.1291
    return round(index, 1)

def count_syllables(word):
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith('e'):
        count -= 1
    if word.endswith('le'):
        count += 1
    if count == 0:
        count += 1
    return count

def calculate_ttr(text):
    words = tokenize_text(text)
    return len(set(words)) / len(words)

def calculate_mtld(text, threshold=0.72):
    words = tokenize_text(text)
    factor_count = 0
    factor_lengths = []
    current_factor = []
    
    for word in words:
        current_factor.append(word)
        ttr = len(set(current_factor)) / len(current_factor)
        if ttr <= threshold:
            factor_count += 1
            factor_lengths.append(len(current_factor))
            current_factor = []
    
    if factor_count == 0:
        return len(words)
    
    mtld = sum(factor_lengths) / factor_count
    return mtld

def calculate_avg_sentence_length(text):
    sentences = sentence_tokenize(text)
    words = tokenize_text(text)
    return len(words) / len(sentences) if sentences else 0

def calculate_clause_density(text):
    sentences = sentence_tokenize(text)
    clause_markers = ['and', 'but', 'because', 'if', 'when', 'while', 'although', 'as', 'since', 'unless', 'though', 'whereas', 'whether']
    clause_count = sum(sum(1 for marker in clause_markers if marker in sentence.lower()) + 1 for sentence in sentences)
    return clause_count / len(sentences) if sentences else 0

def simple_pos_tagger(text):
    words = tokenize_text(text)
    tagged = []
    for word in words:
        if word in ['the', 'a', 'an']:
            tagged.append((word, 'DT'))
        elif word in ['is', 'am', 'are', 'was', 'were']:
            tagged.append((word, 'VB'))
        elif word.endswith('ly'):
            tagged.append((word, 'RB'))
        elif word.endswith('ed'):
            tagged.append((word, 'VBD'))
        elif word.endswith('ing'):
            tagged.append((word, 'VBG'))
        elif word in ['i', 'you', 'he', 'she', 'it', 'we', 'they']:
            tagged.append((word, 'PRP'))
        else:
            tagged.append((word, 'NN'))  # Default to noun
    return tagged

def calculate_pos_distribution(text):
    pos_tags = simple_pos_tagger(text)
    return Counter(tag for word, tag in pos_tags)

def calculate_ngram_frequency(text, n=2):
    words = tokenize_text(text)
    ngrams = [tuple(words[i:i+n]) for i in range(len(words)-n+1)]
    return Counter(ngrams)

def generate_cloze_test(text, num_blanks=5):
    words = tokenize_text(text)
    content_words = [word for word, tag in simple_pos_tagger(text) if tag.startswith(('NN', 'VB', 'JJ', 'RB'))]
    
    if len(content_words) < num_blanks:
        num_blanks = len(content_words)
    
    words_to_blank = random.sample(content_words, num_blanks)
    cloze_text = ' '.join(['_____' if word in words_to_blank else word for word in words])
    return cloze_text, words_to_blank

def analyze_vocabulary(text):
    fk_grade = calculate_flesch_kincaid_grade(text)
    flesch_ease = calculate_flesch_reading_ease(text)
    gunning_fog = calculate_gunning_fog_index(text)
    smog = calculate_smog_index(text)
    ttr = calculate_ttr(text)
    mtld = calculate_mtld(text)
    avg_sentence_length = calculate_avg_sentence_length(text)
    clause_density = calculate_clause_density(text)
    pos_distribution = calculate_pos_distribution(text)
    bigram_freq = calculate_ngram_frequency(text, 2)
    cloze_test, blanked_words = generate_cloze_test(text)
    
    # Determine overall level based on multiple factors
    readability_score = (fk_grade / 12 + (100 - flesch_ease) / 100 + gunning_fog / 18 + smog / 18) / 4
    complexity_score = (
        readability_score * 0.4 +
        (1 - ttr) * 0.2 +
        min(avg_sentence_length / 20, 1) * 0.2 +
        min(clause_density / 3, 1) * 0.1 +
        (pos_distribution.get('VB', 0) / len(tokenize_text(text))) * 0.05 +
        (pos_distribution.get('JJ', 0) / len(tokenize_text(text))) * 0.05
    )
    
    if complexity_score < 0.35:
        overall_level = 'A1'
    elif complexity_score < 0.55:
        overall_level = 'A2'
    elif complexity_score < 0.75:
        overall_level = 'B1'
    else:
        overall_level = 'B2'
    
    return {
        'overall_level': overall_level,
        'flesch_kincaid_grade': fk_grade,
        'flesch_reading_ease': flesch_ease,
        'gunning_fog_index': gunning_fog,
        'smog_index': smog,
        'type_token_ratio': ttr,
        'mtld': mtld,
        'avg_sentence_length': avg_sentence_length,
        'clause_density': clause_density,
        'pos_distribution': dict(pos_distribution),
        'top_bigrams': dict(bigram_freq.most_common(10)),
        'cloze_test': cloze_test,
        'blanked_words': blanked_words,
        'complexity_score': complexity_score
    }

def adjust_vocabulary(text, target_level):
    prompt = f"""
    Adjust the following text to a {target_level} English level:

    {text}

    General Instructions:
    1. Maintain the original meaning and topic of the text as closely as possible.
    2. Adjust vocabulary, grammar, and sentence structure to match the {target_level} level precisely.
    3. Ensure the adjusted text flows naturally and maintains coherence.
    4. If necessary, add brief explanations for concepts that might be challenging for learners at this level.

    Level-Specific Guidelines for {target_level}:

    A1 Level:
    - Use only the most basic and frequent words.
    - Keep sentences very short (5-7 words on average) and simple.
    - Use mainly present simple tense and some basic present continuous.
    - Focus on concrete, everyday topics and familiar situations.
    - Use numbers 1-100 and basic time expressions.
    - Avoid all idioms, phrasal verbs, and complex grammatical structures.

    A2 Level:
    - Use simple vocabulary with some more advanced words introduced in context.
    - Create sentences that are slightly longer than A1 (8-10 words on average).
    - Use present simple, present continuous, past simple, and 'going to' future.
    - Include basic modals (can, must) and comparatives/superlatives.
    - Use basic conjunctions (and, but, because) to connect ideas.
    - Introduce simple idiomatic expressions and common phrasal verbs.

    B1 Level:
    - Use a mix of common and more advanced vocabulary.
    - Combine simple and more complex sentences (12-15 words on average).
    - Use all basic tenses, including present perfect, and introduce past continuous.
    - Include first conditional sentences and relative clauses.
    - Use some idiomatic expressions and phrasal verbs.
    - Introduce passive voice in present and past simple tenses.
    - Discuss both concrete and some abstract topics.

    B2 Level:
    - Use a wide range of vocabulary, including less common words.
    - Create a mix of simple and complex sentences (15-20 words on average).
    - Use all tenses confidently, including past perfect and future perfect.
    - Include second and third conditional sentences.
    - Use a variety of complex structures, including cleft sentences and inversion.
    - Incorporate idiomatic expressions, colloquialisms, and phrasal verbs naturally.
    - Discuss abstract concepts and hypothetical situations.
    - Use passive voice across various tenses and with modals.

    Adjusted text:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in adjusting texts to specific CEFR English proficiency levels, ensuring the content remains engaging and informative while meeting the target level requirements."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred during text adjustment: {e}")
        return text  # Return original text if adjustment fails

