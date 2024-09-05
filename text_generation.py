from openai import OpenAI
import os
import random
import re
from vocabulary_analysis import analyze_vocabulary

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Base prompt template
BASE_PROMPT_TEMPLATE = """
    Generate a {length} passage on the topic of {topic}.
    The passage should be informative, engaging, and tailored for an English language learner at {level} level.

    Content Guidelines:
    1. Begin with a clear introduction to the topic.
    2. Develop 2-3 main points or ideas related to the topic.
    3. Use examples or anecdotes to illustrate key concepts when appropriate.
    4. Conclude with a brief summary or thought-provoking statement.

    Language Requirements:
    1. Use vocabulary appropriate for {level} level learners.
    2. Employ grammatical structures suitable for {level} level.
    3. Maintain an average sentence length of {avg_sentence_length} words.
    4. Include a variety of sentence types (simple, compound, complex) as appropriate for the level.
    5. Use {tense_instructions}
    6. Incorporate {num_target_vocab} topic-specific vocabulary words.

    Text Structure:
    1. Organize the content into {num_paragraphs} clear paragraphs.
    2. Use transition words and phrases to connect ideas smoothly.
    3. Ensure the text flows logically from one point to the next.

    Additional Instructions:
    {level_specific_instructions}

    Ensure the text is between {min_words} and {max_words} words long.
    """
# Level-specific instructions
LEVEL_INSTRUCTIONS = {
    "A1": """
    1. Vocabulary: Use only the most basic and common words. Introduce no more than 5-7 new words related to the topic.
    2. Grammar: Stick to simple present tense, basic present continuous, and simple imperatives. Avoid complex structures.
    3. Sentences: Keep sentences very short and simple. Aim for 5-7 words per sentence on average.
    4. Content: Focus on concrete, everyday topics. Use familiar contexts and situations.
    5. Structure: Use mostly simple sentences. Limit compound sentences to those joined with 'and' or 'but'.
    6. Numbers and Time: Use numbers 1-100, days of the week, months, and very basic time expressions.
    7. Questions: Include 1-2 basic yes/no or wh- questions using 'what', 'where', or 'when'.
    8. Repetition: Repeat key words and phrases for reinforcement.
    9. Instructions: Include 1-2 very simple imperative sentences (e.g., "Look at the picture." "Write the word.")
    10. Avoid: Idioms, phrasal verbs, passive voice, and hypothetical situations.
    """,
    "A2": """
    1. Vocabulary: Use common words with some more advanced vocabulary. Introduce 8-10 new topic-related words.
    2. Grammar: Use present simple, present continuous, past simple, and future with 'going to'. Introduce basic modals (can, must).
    3. Sentences: Aim for slightly longer sentences, about 8-10 words on average. Mix simple and compound sentences.
    4. Content: Cover familiar topics but with more detail. Introduce some basic abstract concepts.
    5. Structure: Use a mix of simple and compound sentences. Introduce basic complex sentences with 'because' or 'when'.
    6. Numbers and Time: Use larger numbers, more detailed time expressions, and basic frequency adverbs (always, sometimes, never).
    7. Questions: Include 2-3 questions, mixing yes/no and wh- questions. Introduce 'how' questions.
    8. Comparatives and Superlatives: Use basic comparative and superlative forms of adjectives.
    9. Sequencing: Use basic sequencing words (first, then, after that, finally).
    10. Avoid: Complex idioms, most phrasal verbs, passive voice in past tense.
    """,
    "B1": """
    1. Vocabulary: Use a mix of common and more advanced words. Introduce 12-15 new topic-related words or phrases.
    2. Grammar: Use all basic tenses, including present perfect. Introduce past continuous and basic conditionals (first conditional).
    3. Sentences: Aim for an average of 12-15 words per sentence. Use a variety of sentence structures.
    4. Content: Discuss both concrete and some abstract topics. Include some opinion-based content.
    5. Structure: Use a balance of simple, compound, and complex sentences. Introduce relative clauses.
    6. Expressions: Incorporate some idiomatic expressions and common phrasal verbs.
    7. Questions: Include 3-4 varied question types, including indirect questions.
    8. Passive Voice: Introduce passive voice in present and past simple tenses.
    9. Modals: Use a range of modal verbs for advice, possibility, and obligation.
    10. Avoid: Highly specialized vocabulary, complex literary devices, and very formal language.
    """,
    "B2": """
    1. Vocabulary: Use a wide range of vocabulary, including some less common words. Introduce 15-20 new topic-related words or phrases.
    2. Grammar: Use all tenses confidently, including past perfect and future perfect. Use second and third conditionals.
    3. Sentences: Vary sentence length, with an average of 15-20 words. Use a wide variety of complex structures.
    4. Content: Discuss abstract concepts and hypothetical situations. Include detailed arguments or analysis.
    5. Structure: Use a full range of simple, compound, and complex sentences. Include cleft sentences and inversion for emphasis.
    6. Expressions: Use idiomatic expressions, colloquialisms, and a wide range of phrasal verbs naturally.
    7. Questions: Include tag questions, embedded questions, and questions used rhetorically.
    8. Passive Voice: Use passive voice across various tenses and with modals.
    9. Literary Devices: Incorporate some metaphors, similes, and other figurative language where appropriate.
    10. Avoid: Overly simplistic language or structures. Challenge the reader while maintaining clarity.
    """
}

def create_prompt(topic, level, length):
    level_specific_instructions = LEVEL_INSTRUCTIONS.get(level, "")
    try:
        min_words, max_words = map(int, re.findall(r'\d+', length))
        
        # Define level-specific parameters
        if level == 'A1':
            avg_sentence_length = "5-7"
            num_paragraphs = "2-3"
            tense_instructions = "mainly present simple tense and some basic present continuous"
            num_target_vocab = "5-7"
        elif level == 'A2':
            avg_sentence_length = "8-10"
            num_paragraphs = "3-4"
            tense_instructions = "present simple, present continuous, past simple, and 'going to' future"
            num_target_vocab = "8-10"
        elif level == 'B1':
            avg_sentence_length = "12-15"
            num_paragraphs = "4-5"
            tense_instructions = "all basic tenses, including present perfect and past continuous"
            num_target_vocab = "12-15"
        else:  # B2
            avg_sentence_length = "15-20"
            num_paragraphs = "5-6"
            tense_instructions = "all tenses, including past perfect and future perfect"
            num_target_vocab = "15-20"
        
        return BASE_PROMPT_TEMPLATE.format(
            topic=topic,
            level=level,
            length=length,
            level_specific_instructions=level_specific_instructions,
            min_words=min_words,
            max_words=max_words,
            avg_sentence_length=avg_sentence_length,
            num_paragraphs=num_paragraphs,
            tense_instructions=tense_instructions,
            num_target_vocab=num_target_vocab
        )
    except ValueError as e:
        print(f"Error parsing word count range: {e}. Using default range.")
        return BASE_PROMPT_TEMPLATE.format(
            topic=topic,
            level=level,
            length=length,
            level_specific_instructions=level_specific_instructions,
            min_words=50,
            max_words=300,
            avg_sentence_length="10-15",
            num_paragraphs="3-4",
            tense_instructions="appropriate tenses for the level",
            num_target_vocab="10-15"
        )

def generate_text(prompt, max_tokens=400, temperature=0.7):
    system_message = """
    You are an advanced AI language model specialized in generating high-quality, 
    level-appropriate content for English language learners. Your task is to create text that is:
    1. Precisely tailored to the specified CEFR level (A1, A2, B1, or B2)
    2. Engaging and informative on the given topic
    3. Structured appropriately for the target level
    4. Using vocabulary and grammar suitable for the specified level
    5. Meeting the required length constraints

    Follow these additional guidelines:
    - Adhere strictly to the level-specific instructions provided
    - Ensure natural flow and coherence throughout the text
    - Include level-appropriate cultural references when relevant
    - Provide context or brief explanations for potentially unfamiliar concepts
    - Use authentic language that a learner might encounter in real-life situations
    - Incorporate opportunities for learners to infer meaning from context
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred during text generation: {e}")
        return None

def generate_topic_based_text(topic, level, text_length, max_attempts=3):
    length_mapping = {
        "Short (100-150 words)": "short (100-150 words)",
        "Medium (150-250 words)": "medium-length (150-250 words)",
        "Long (250-350 words)": "long (250-350 words)"
    }
    prompt = create_prompt(topic, level, length_mapping[text_length])
    
    for attempt in range(max_attempts):
        text = generate_text(prompt)
        if text:
            word_count = len(text.split())
            analysis = analyze_vocabulary(text)
            print(f"Attempt {attempt + 1}:")
            print(f"Generated text length: {word_count} words")
            print(f"Analyzed level: {analysis['overall_level']}")
            print(f"Complexity score: {analysis['complexity_score']:.2f}")
            print(f"Flesch-Kincaid Grade: {analysis['flesch_kincaid_grade']:.2f}")
            
            # Check if the text meets the length criteria
            try:
                min_words, max_words = map(int, re.findall(r'\d+', length_mapping[text_length]))
                if min_words <= word_count <= max_words and analysis['overall_level'] == level:
                    return text, analysis
                else:
                    print(f"Generated text did not meet criteria. Retrying...")
            except ValueError as e:
                print(f"Error parsing word count range: {e}. Retrying...")
        else:
            print(f"Attempt {attempt + 1}: Failed to generate text. Retrying...")
    
    print(f"Failed to generate appropriate text after {max_attempts} attempts.")
    return None, None

def get_random_topic():
    topics = ["Travel", "Technology", "Food", "Sports", "Music", "Nature", "Art", "Science", "History", "Culture"]
    return random.choice(topics)
