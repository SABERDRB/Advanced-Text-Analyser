# Advanced Text Analyzer 

This project is an advanced tool for analyzing and adjusting text based on different English proficiency levels (CEFR levels: A1, A2, B1, B2). It provides a user-friendly interface for generating level-appropriate texts, analyzing existing texts, and adjusting texts to different proficiency levels.

## Features

- Text generation based on topics and target English levels
- Comprehensive text analysis including:
  - Readability scores (Flesch-Kincaid, Flesch Reading Ease, Gunning Fog, SMOG)
  - Lexical diversity measures (TTR, MTLD)
  - Syntactic complexity (Average Sentence Length, Clause Density)
  - N-gram analysis (Top Bigrams)
  - Part-of-Speech distribution
  - Cloze test generation
- Text level adjustment to target CEFR levels
- Interactive Streamlit web interface

## Installation

1. Clone this repository
 

2. Install the required dependencies


3. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

## Usage

Run the Streamlit app:

```
streamlit run app.py
```

Then open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).

## Project Structure

- `app.py`: Main Streamlit application
- `text_generation.py`: Functions for generating level-appropriate text
- `vocabulary_analysis.py`: Functions for analyzing and adjusting text complexity

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT model used in text generation and adjustment
- Streamlit for the web application framework
