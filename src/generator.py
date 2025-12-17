from openai import OpenAI
import json
import typing_extensions as typing

class QuizQuestion(typing.TypedDict):
    question: str
    answer: str
    options: list[str]

class QuizGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = 'gpt-4o-mini'

    def generate_quiz(self, transcript_text: str, num_questions: int = 50, max_chars_per_chunk: int = 25000, 
                      questions_per_batch_target: int = 5, on_progress: typing.Callable[[int, int], None] = None) -> list[QuizQuestion]:
        """
        Generates quiz questions from the full transcript, processing in batches to ensure coverage
        and handle large texts.
        """
        import math

        # Strategy:
        # 1. Determine number of batches based on length and desired question count.
        #    - A reasonable chunk size for context is ~50k chars (approx 12k tokens).
        #    - We also want to avoid asking for too many questions in one prompt (e.g. > 5-10).
        # 2. Split text into that many segments.
        # 3. Request a portion of num_questions from each segment.

        total_chars = len(transcript_text)
        batches_by_len = math.ceil(total_chars / max_chars_per_chunk)
        batches_by_q = math.ceil(num_questions / questions_per_batch_target)
        
        num_batches = max(batches_by_len, batches_by_q)
        
        # Calculate roughly equal chunk sizes
        chunk_size = math.ceil(total_chars / num_batches)
        
        all_questions = []
        questions_generated_so_far = 0

        for i in range(num_batches):
            if on_progress:
                on_progress(i, num_batches)

            # Calculate slice
            start = i * chunk_size
            end = min((i + 1) * chunk_size, total_chars)
            chunk_text = transcript_text[start:end]
            
            # Determine how many questions to ask for this batch
            # We distribute the remaining needed questions among the remaining batches
            remaining_batches = num_batches - i
            questions_needed_total = num_questions - questions_generated_so_far
            
            if questions_needed_total <= 0:
                break
                
            # Distribute evenly
            q_for_this_batch = math.ceil(questions_needed_total / remaining_batches)
            
            # If chunk is too small/empty (edge case), skip
            if not chunk_text.strip():
                continue

            batch_qs = self._generate_batch(chunk_text, q_for_this_batch)
            all_questions.extend(batch_qs)
            questions_generated_so_far += len(batch_qs)

        if on_progress:
            on_progress(num_batches, num_batches)

        return all_questions

    def _generate_batch(self, text: str, num_questions: int) -> list[QuizQuestion]:
        prompt = f"""
        You are an expert University Professor creating a rigorous exam to test deep conceptual understanding of the following material.
        The content is technical (e.g., Computer Science, LLMs, Mathematics).
        
        Your Goal: Create {num_questions} high-quality multiple-choice questions based on the concepts discussed in the transcript segment.
        
        Crucial Guidelines:
        1. **Test Knowledge, Not Recall**: Do NOT ask "What did the speaker say?" or "What example was used?". Instead, ask about the concepts, underlying principles, and mechanisms.
        2. **Focus on "Why" and "How"**: Questions should probe the logic, implications, trade-offs, and causality of the ideas presented.
        3. **Synthesize**: Questions should require integrating information to find the correct answer, not just text matching.
        4. **Plausible Distractors**: Ensure incorrect options (distractors) are conceptually relevant but arguably wrong, requiring precise understanding to rule out.
        
        Return the result as a JSON object with a key "questions" which is a list of objects, where each object has:
        - "question": The question text
        - "answer": The correct answer text (must be one of the options)
        - "options": A list of 4 possible answers
        
        Transcript Segment:
        {text}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates quiz questions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                return data.get("questions", [])
            return []
        except Exception as e:
            print(f"Error generating quiz batch: {e}")
            return []
