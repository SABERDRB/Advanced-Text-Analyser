import streamlit as st
from text_generation import generate_topic_based_text, get_random_topic
from vocabulary_analysis import analyze_vocabulary, adjust_vocabulary
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
import pandas as pd

# Load environment variables
load_dotenv()



def create_level_plot(level):
    levels = ['A1', 'A2', 'B1', 'B2']
    values = [1 if l == level else 0 for l in levels]
    
    fig = go.Figure(data=[go.Bar(
        x=levels,
        y=values,
        marker_color=['royalblue' if v == 1 else 'lightgray' for v in values]
    )])
    
    fig.update_layout(
        title='Text Level',
        xaxis_title='CEFR Level',
        yaxis_title='',
        showlegend=False,
        height=300,
        yaxis=dict(range=[0, 1.1], showticklabels=False)
    )
    
    return fig 

def adjust_text_with_attempts(text, target_level, max_attempts=5):
    for attempt in range(max_attempts):
        adjusted_text = adjust_vocabulary(text, target_level)
        analysis = analyze_vocabulary(adjusted_text)
        if analysis['overall_level'] == target_level:
            return adjusted_text, analysis, attempt + 1
        # If reached the last attempt and still haven't matched the target level,
        # return the last adjusted text anyway
        if attempt == max_attempts - 1:
            return adjusted_text, analysis, max_attempts

    return text, analyze_vocabulary(text), max_attempts

if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set your OpenAI API key in the .env file.")
    st.stop()

# Constants
TOPICS = ["Travel", "Technology", "Food", "Sports", "Music", "Nature", "Art", "Science", "History", "Culture", "Random"]
LEVELS = ["A1", "A2", "B1", "B2"]
TEXT_LENGTHS = ["Short (100-150 words)", "Medium (150-250 words)", "Long (250-350 words)"]

# Set page config
st.set_page_config(page_title="Advanced Text Analyzer and Adjuster", page_icon="📚", layout="wide")

st.title("Advanced Text Analyzer and Adjuster")

# Initialize session state
if 'generated_text' not in st.session_state:
    st.session_state.generated_text = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'target_level' not in st.session_state:
    st.session_state.target_level = None
if 'text_length' not in st.session_state:
    st.session_state.text_length = "Medium (100-200 words)"

# Sidebar for user inputs
with st.sidebar:
    st.header("Generate Text")
    selected_topic = st.selectbox("Choose a topic:", TOPICS)
    target_level = st.selectbox("Target English level:", LEVELS)
    text_length = st.selectbox("Choose text length:", TEXT_LENGTHS)
    max_attempts = st.slider("Maximum generation attempts:", min_value=1, max_value=20, value=10)
    generate_button = st.button("Generate Text")

# Function to create a radar chart
def create_radar_chart(analysis_result, title):
    categories = ['Readability', 'Lexical Diversity', 'Sentence Length', 'Clause Density', 'Verb Usage', 'Adjective Usage']
    
    pos_distribution = analysis_result['pos_distribution']
    total_words = sum(pos_distribution.values())
    
    values = [
        (12 - analysis_result['flesch_kincaid_grade']) / 12,  # Normalize and invert FK grade
        analysis_result['type_token_ratio'],
        min(analysis_result['avg_sentence_length'] / 20, 1),  # Normalize to 0-1 range
        min(analysis_result['clause_density'] / 3, 1),  # Normalize to 0-1 range
        pos_distribution.get('VB', 0) / total_words if total_words > 0 else 0,
        pos_distribution.get('JJ', 0) / total_words if total_words > 0 else 0
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title=title
    )
    
    return fig

if generate_button:
    attempt = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    debug_expander = st.expander("Debug Information")

    if selected_topic == "Random":
        selected_topic = get_random_topic()
        st.info(f"Randomly selected topic: {selected_topic}")

    while attempt < max_attempts:
        attempt += 1
        status_text.text(f"Attempt {attempt}/{max_attempts}: Generating and analyzing text...")
        progress_bar.progress(attempt / max_attempts)

        try:
            generated_text, analysis_result = generate_topic_based_text(selected_topic, target_level, text_length)
            if generated_text is None:
                raise Exception("Failed to generate text")
            
            with debug_expander:
                st.write(f"Attempt {attempt} Debug Info:")
                st.write(f"Generated text length: {len(generated_text.split())} words")
                st.write(f"Analyzed level: {analysis_result['overall_level']}")
                st.write(f"Complexity score: {analysis_result['complexity_score']:.2f}")
                st.write(f"Flesch-Kincaid Grade: {analysis_result['flesch_kincaid_grade']:.2f}")
            
            if analysis_result['overall_level'] == target_level:
                status_text.text(f"Success! Text generated at target level {target_level} on attempt {attempt}.")
                st.session_state.generated_text = generated_text
                st.session_state.analysis_result = analysis_result
                st.session_state.target_level = target_level
                st.session_state.text_length = text_length
                break
            else:
                status_text.text(f"Generated text did not meet target level. Retrying...")
        except Exception as e:
            st.error(f"An error occurred on attempt {attempt}: {str(e)}")
            continue

    progress_bar.empty()

if st.session_state.generated_text and st.session_state.analysis_result['overall_level'] == st.session_state.target_level:
    st.subheader("Generated Text")
    st.write(st.session_state.generated_text)
    st.write(f"Text length: {len(st.session_state.generated_text.split())} words")

    st.subheader("Text Analysis")
    st.write(f"The overall text level is: {st.session_state.analysis_result['overall_level']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Readability Scores:")
        readability_df = pd.DataFrame({
            'Metric': ['Flesch-Kincaid Grade', 'Flesch Reading Ease', 'Gunning Fog Index', 'SMOG Index'],
            'Score': [
                st.session_state.analysis_result['flesch_kincaid_grade'],
                st.session_state.analysis_result['flesch_reading_ease'],
                st.session_state.analysis_result['gunning_fog_index'],
                st.session_state.analysis_result['smog_index']
            ]
        })
        st.table(readability_df.set_index('Metric'))

        st.write("Lexical Diversity:")
        st.write(f"Type-Token Ratio: {st.session_state.analysis_result['type_token_ratio']:.2f}")
        st.write(f"MTLD: {st.session_state.analysis_result['mtld']:.2f}")

        st.write("Syntactic Complexity:")
        st.write(f"Average Sentence Length: {st.session_state.analysis_result['avg_sentence_length']:.2f}")
        st.write(f"Clause Density: {st.session_state.analysis_result['clause_density']:.2f}")
    
    with col2:
        st.plotly_chart(create_radar_chart(st.session_state.analysis_result, "Text Complexity Analysis"))
        st.plotly_chart(create_level_plot(st.session_state.analysis_result['overall_level']))

        st.write("Top Bigrams:")
        bigrams_df = pd.DataFrame(list(st.session_state.analysis_result['top_bigrams'].items()), columns=['Bigram', 'Frequency'])
        st.table(bigrams_df)

    st.subheader("Cloze Test")
    st.write(st.session_state.analysis_result['cloze_test'])
    st.write("Blanked words:", ", ".join(st.session_state.analysis_result['blanked_words']))

    # Section for adjusting the generated text level
    st.subheader("Adjust Generated Text Level")
    new_level_generated = st.selectbox("Select new level for generated text:", LEVELS, index=LEVELS.index(st.session_state.target_level), key="generated_text_new_level")
    adjust_button_generated = st.button("Adjust Generated Text", key="generated_text_adjust_button")

    if adjust_button_generated:
        adjusted_text, adjusted_analysis, attempts = adjust_text_with_attempts(st.session_state.generated_text, new_level_generated)
        
        st.subheader(f"Adjusted Generated Text (Level: {new_level_generated})")
        st.write(adjusted_text)
        
        st.subheader("Adjusted Generated Text Analysis")
        st.write(f"The adjusted text level is: {adjusted_analysis['overall_level']}")
        st.write(f"Attempts needed: {attempts}")
        
        adj_col1, adj_col2 = st.columns(2)
        
        with adj_col1:
            st.write("Adjusted Readability Scores:")
            adj_readability_df = pd.DataFrame({
                'Metric': ['Flesch-Kincaid Grade', 'Flesch Reading Ease', 'Gunning Fog Index', 'SMOG Index'],
                'Score': [
                    adjusted_analysis['flesch_kincaid_grade'],
                    adjusted_analysis['flesch_reading_ease'],
                    adjusted_analysis['gunning_fog_index'],
                    adjusted_analysis['smog_index']
                ]
            })
            st.table(adj_readability_df.set_index('Metric'))

            st.write("Adjusted Lexical Diversity:")
            st.write(f"Type-Token Ratio: {adjusted_analysis['type_token_ratio']:.2f}")
            st.write(f"MTLD: {adjusted_analysis['mtld']:.2f}")
        
        with adj_col2:
            st.plotly_chart(create_radar_chart(adjusted_analysis, "Adjusted Generated Text Complexity Analysis"))
            st.plotly_chart(create_level_plot(adjusted_analysis['overall_level']))

if 'user_input_text' not in st.session_state:
    st.session_state.user_input_text = ""
if 'user_analysis_result' not in st.session_state:
    st.session_state.user_analysis_result = None

st.markdown("---")

# Analyze Your Own Text section
st.header("Analyze Your Own Text")
user_text = st.text_area("Enter your text here:", height=200)
analyze_button = st.button("Analyze Text")

if analyze_button and user_text:
    st.session_state.user_input_text = user_text  # Store the user input in session state
    st.session_state.user_analysis_result = analyze_vocabulary(user_text)  # Store the analysis result in session state

if st.session_state.user_analysis_result:
    st.subheader("Text Analysis")
    st.write(f"The overall text level is: {st.session_state.user_analysis_result['overall_level']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Readability Scores:")
        readability_df = pd.DataFrame({
            'Metric': ['Flesch-Kincaid Grade', 'Flesch Reading Ease', 'Gunning Fog Index', 'SMOG Index'],
            'Score': [
                st.session_state.user_analysis_result['flesch_kincaid_grade'],
                st.session_state.user_analysis_result['flesch_reading_ease'],
                st.session_state.user_analysis_result['gunning_fog_index'],
                st.session_state.user_analysis_result['smog_index']
            ]
        })
        st.table(readability_df.set_index('Metric'))

        st.write("Lexical Diversity:")
        st.write(f"Type-Token Ratio: {st.session_state.user_analysis_result['type_token_ratio']:.2f}")
        st.write(f"MTLD: {st.session_state.user_analysis_result['mtld']:.2f}")

        st.write("Syntactic Complexity:")
        st.write(f"Average Sentence Length: {st.session_state.user_analysis_result['avg_sentence_length']:.2f}")
        st.write(f"Clause Density: {st.session_state.user_analysis_result['clause_density']:.2f}")
    
    with col2:
        st.plotly_chart(create_radar_chart(st.session_state.user_analysis_result, "Text Complexity Analysis"))
        st.plotly_chart(create_level_plot(st.session_state.user_analysis_result['overall_level']))
        st.write("Top Bigrams:")
        bigrams_df = pd.DataFrame(list(st.session_state.user_analysis_result['top_bigrams'].items()), columns=['Bigram', 'Frequency'])
        st.table(bigrams_df)

    st.subheader("Cloze Test")
    st.write(st.session_state.user_analysis_result['cloze_test'])
    st.write("Blanked words:", ", ".join(st.session_state.user_analysis_result['blanked_words']))

    # Section for adjusting the user input text level
    st.subheader("Adjust User Input Text Level")
    new_level_user = st.selectbox("Select new level for user input text:", LEVELS, index=LEVELS.index(st.session_state.user_analysis_result['overall_level']), key="user_text_new_level")
    adjust_button_user = st.button("Adjust User Input Text", key="user_text_adjust_button")

    if adjust_button_user:
        adjusted_text, adjusted_analysis, attempts = adjust_text_with_attempts(st.session_state.user_input_text, new_level_user)
        
        st.subheader(f"Adjusted User Input Text (Level: {new_level_user})")
        st.write(adjusted_text)
        
        st.subheader("Adjusted User Input Text Analysis")
        st.write(f"The adjusted text level is: {adjusted_analysis['overall_level']}")
        st.write(f"Attempts needed: {attempts}")
        
        adj_col1, adj_col2 = st.columns(2)
        
        with adj_col1:
            st.write("Adjusted Readability Scores:")
            adj_readability_df = pd.DataFrame({
                'Metric': ['Flesch-Kincaid Grade', 'Flesch Reading Ease', 'Gunning Fog Index', 'SMOG Index'],
                'Score': [
                    adjusted_analysis['flesch_kincaid_grade'],
                    adjusted_analysis['flesch_reading_ease'],
                    adjusted_analysis['gunning_fog_index'],
                    adjusted_analysis['smog_index']
                ]
            })
            st.table(adj_readability_df.set_index('Metric'))

            st.write("Adjusted Lexical Diversity:")
            st.write(f"Type-Token Ratio: {adjusted_analysis['type_token_ratio']:.2f}")
            st.write(f"MTLD: {adjusted_analysis['mtld']:.2f}")
        
        with adj_col2:
            st.plotly_chart(create_radar_chart(adjusted_analysis, "Adjusted User Input Text Complexity Analysis"))
            st.plotly_chart(create_level_plot(adjusted_analysis['overall_level']))
            
# Additional information
st.sidebar.markdown("---")
st.sidebar.info("""
This advanced text analyzer and adjuster generates text on a given topic and provides comprehensive analysis of its complexity.

How to use:
1. Select a topic (or choose 'Random' for a surprise) and target English level.
2. Choose the desired text length.
3. Adjust the maximum number of generation attempts if desired.
4. Click 'Generate Text' to create a passage at the target level and length.
5. View the generated text and its comprehensive analysis.
6. Optionally, adjust the generated text to a different level.
7. Alternatively, enter your own text in the 'Analyze Your Own Text' section at the bottom of the page.
8. Click 'Analyze Text' to see the analysis of your input.
9. Optionally, adjust your input text to a different level.

The analysis includes:
- Readability scores (Flesch-Kincaid, Flesch Reading Ease, Gunning Fog, SMOG)
- Lexical diversity measures (TTR, MTLD)
- Syntactic complexity (Avg. Sentence Length, Clause Density)
- N-gram analysis (Top Bigrams)
- Part-of-Speech distribution
- Cloze test generation
""")

# Footer
st.markdown("---")
st.markdown("Created with Streamlit, OpenAI GPT, and advanced NLP techniques")