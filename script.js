document.addEventListener('DOMContentLoaded', () => {
    const subjectSelect = document.getElementById('subject-select');
    const chapterSelect = document.getElementById('chapter-select');
    const questionLimitInput = document.getElementById('question-limit');
    const startQuizBtn = document.getElementById('start-quiz-btn');
    const quizSetupDiv = document.getElementById('quiz-setup');
    const quizAreaDiv = document.getElementById('quiz-area');
    const resultAreaDiv = document.getElementById('result-area');
    const currentQuestionNumber = document.getElementById('current-question-number');
    const questionText = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    const submitQuizBtn = document.getElementById('submit-quiz-btn');
    const scoreDisplay = document.getElementById('score-display');
    const detailedResultsDiv = document.getElementById('detailed-results');
    const restartQuizBtn = document.getElementById('restart-quiz-btn');

    let currentQuiz = [];
    let currentQuestionIndex = 0;
    let userAnswers = [];
    let questionStartTime;

    const chapters = {
        botany: ["Plant Kingdom", "Photosynthesis", "Cell Cycle", "Mineral Nutrition", "Reproduction in Flowering Plants"],
        zoology: ["Animal Kingdom", "Human Physiology", "Genetics and Evolution", "Human Reproduction", "Digestion and Absorption"],
        physics: ["Mechanics", "Electromagnetism", "Optics", "Modern Physics", "Thermodynamics"],
        chemistry: ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry", "Atomic Structure", "Chemical Bonding"]
    };

    function updateStartButtonState() {
        const isSubjectSelected = subjectSelect.value !== '';
        const isChapterSelected = chapterSelect.value !== '';
        startQuizBtn.disabled = !(isSubjectSelected && isChapterSelected);
    }

    subjectSelect.addEventListener('change', () => {
        const selectedSubject = subjectSelect.value;
        chapterSelect.innerHTML = '<option value="">-- Select Chapter --</option>';
        chapterSelect.disabled = true;

        if (selectedSubject && chapters[selectedSubject]) {
            chapters[selectedSubject].forEach(chapter => {
                const option = document.createElement('option');
                option.value = chapter;
                option.textContent = chapter;
                chapterSelect.appendChild(option);
            });
            chapterSelect.disabled = false;
        }
        updateStartButtonState();
    });

    chapterSelect.addEventListener('change', updateStartButtonState);

    startQuizBtn.addEventListener('click', async () => {
        const selectedSubject = subjectSelect.value;
        const selectedChapter = chapterSelect.value;
        const questionLimit = parseInt(questionLimitInput.value);

        if (!selectedSubject || !selectedChapter || isNaN(questionLimit) || questionLimit < 1) {
            alert("Please select subject, chapter, and a valid number of questions.");
            return;
        }

        startQuizBtn.textContent = 'Generating Quiz...';
        startQuizBtn.disabled = true;

        try {
            const response = await fetch('https://vipquiz-2.onrender.com/generate_quiz', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    subject: selectedSubject,
                    chapter: selectedChapter,
                    limit: questionLimit
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            currentQuiz = data.questions;

            if (currentQuiz.length === 0) {
                alert("No questions were generated. Please try different parameters or check backend logs.");
                throw new Error("Empty quiz generated.");
            }

            currentQuestionIndex = 0;
            userAnswers = [];

            quizSetupDiv.style.display = 'none';
            quizAreaDiv.style.display = 'block';
            displayQuestion(currentQuestionIndex);

        } catch (error) {
            console.error("Error generating quiz:", error);
            alert(`Failed to generate quiz: ${error.message}. Please ensure the backend server is running and check its console for errors.`);
            startQuizBtn.textContent = 'Start Quiz';
            startQuizBtn.disabled = false;
            updateStartButtonState();
        }
    });

    function displayQuestion(index) {
        if (index >= currentQuiz.length) {
            submitQuiz();
            return;
        }

        const question = currentQuiz[index];
        currentQuestionNumber.textContent = `Question ${index + 1} of ${currentQuiz.length}`;
        questionText.innerHTML = question.question;
        optionsContainer.innerHTML = '';

        const shuffledOptions = [...question.options].sort(() => Math.random() - 0.5);

        shuffledOptions.forEach((option, i) => {
            const label = document.createElement('label');
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'question-option';
            radio.value = option;
            label.appendChild(radio);
            label.appendChild(document.createTextNode(option));
            optionsContainer.appendChild(label);
        });

        if (index === currentQuiz.length - 1) {
            nextQuestionBtn.style.display = 'none';
            submitQuizBtn.style.display = 'block';
        } else {
            nextQuestionBtn.style.display = 'block';
            submitQuizBtn.style.display = 'none';
        }

        questionStartTime = Date.now();
    }

    function recordAnswer() {
        const selectedOption = document.querySelector('input[name="question-option"]:checked');
        const timeTaken = Date.now() - questionStartTime;

        userAnswers.push({
            questionId: currentQuiz[currentQuestionIndex].id,
            questionText: currentQuiz[currentQuestionIndex].question,
            selectedAnswer: selectedOption ? selectedOption.value : null,
            correctAnswer: currentQuiz[currentQuestionIndex].correctAnswer,
            timeTaken: timeTaken,
            solution: currentQuiz[currentQuestionIndex].solution
        });
    }

    nextQuestionBtn.addEventListener('click', () => {
        if (!document.querySelector('input[name="question-option"]:checked')) {
            alert('Please select an option before moving to the next question.');
            return;
        }
        recordAnswer();
        currentQuestionIndex++;
        displayQuestion(currentQuestionIndex);
    });

    submitQuizBtn.addEventListener('click', () => {
        if (!document.querySelector('input[name="question-option"]:checked')) {
            alert('Please select an option before submitting the quiz.');
            return;
        }
        recordAnswer();
        submitQuiz();
    });

    async function submitQuiz() {
        quizAreaDiv.style.display = 'none';
        resultAreaDiv.style.display = 'block';

        let score = 0;
        detailedResultsDiv.innerHTML = 'Analyzing results with AI...';

        try {
            const analysisResponse = await fetch('https://vipquiz-2.onrender.com/analyze_results', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    quiz: currentQuiz,
                    userAnswers: userAnswers
                })
            });

            if (!analysisResponse.ok) {
                throw new Error(`HTTP error! Status: ${analysisResponse.status}`);
            }

            const analysisData = await analysisResponse.json();
            detailedResultsDiv.innerHTML = '';

            userAnswers.forEach((answer, index) => {
                const isCorrect = answer.selectedAnswer === answer.correctAnswer;
                if (isCorrect) {
                    score++;
                }

                const resultItem = document.createElement('div');
                resultItem.classList.add('result-item');
                resultItem.innerHTML = `
                    <h4>Question ${index + 1}: ${answer.questionText}</h4>
                    <p>Your Answer: <span class="${isCorrect ? 'correct-answer' : 'wrong-answer'}">${answer.selectedAnswer || 'Not Answered'}</span></p>
                    <p>Correct Answer: <span class="correct-answer">${answer.correctAnswer}</span></p>
                    ${!isCorrect ? `<p><strong>AI Solution:</strong> ${answer.solution || 'Solution not available.'}</p>` : ''}
                    <p>Time Taken: ${(answer.timeTaken / 1000).toFixed(1)} seconds</p>
                `;
                detailedResultsDiv.appendChild(resultItem);
            });

            if (analysisData.overallFeedback) {
                const feedbackDiv = document.createElement('div');
                feedbackDiv.classList.add('result-item');
                feedbackDiv.innerHTML = `<h3>Overall AI Feedback:</h3><p>${analysisData.overallFeedback}</p>`;
                detailedResultsDiv.prepend(feedbackDiv);
            }

        } catch (error) {
            console.error("Error fetching detailed analysis:", error);
            detailedResultsDiv.innerHTML = '<p style="color: red;">Failed to get detailed AI analysis. Displaying basic results.</p>';
            userAnswers.forEach((answer, index) => {
                const isCorrect = answer.selectedAnswer === answer.correctAnswer;
                if (isCorrect) score++;
                const resultItem = document.createElement('div');
                resultItem.classList.add('result-item');
                resultItem.innerHTML = `
                    <h4>Question ${index + 1}: ${answer.questionText}</h4>
                    <p>Your Answer: <span class="${isCorrect ? 'correct-answer' : 'wrong-answer'}">${answer.selectedAnswer || 'Not Answered'}</span></p>
                    <p>Correct Answer: <span class="correct-answer">${answer.correctAnswer}</span></p>
                    <p>Time Taken: ${(answer.timeTaken / 1000).toFixed(1)} seconds</p>
                `;
                detailedResultsDiv.appendChild(resultItem);
            });
        }

        scoreDisplay.textContent = `You scored ${score} out of ${currentQuiz.length}!`;
        startQuizBtn.textContent = 'Start Quiz';
        updateStartButtonState();
    }

    restartQuizBtn.addEventListener('click', () => {
        resultAreaDiv.style.display = 'none';
        quizSetupDiv.style.display = 'block';
        subjectSelect.value = '';
        chapterSelect.innerHTML = '<option value="">-- Select Chapter --</option>';
        chapterSelect.disabled = true;
        questionLimitInput.value = 10;
        updateStartButtonState();
    });

    updateStartButtonState();
});
