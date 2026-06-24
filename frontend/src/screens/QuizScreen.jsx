import { useState, useEffect } from 'react'
import { startAttempt, submitAttempt } from '../api/attempts'

export default function QuizScreen({ groupId, onComplete, onBack }) {
  const [attemptId, setAttemptId] = useState(null)
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [responses, setResponses] = useState({})
  const [skipped, setSkipped] = useState(new Set())
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function init() {
      try {
        const data = await startAttempt(groupId)
        setAttemptId(data.attempt_id)
        setQuestions(data.questions)
      } catch {
        setError('Failed to load questions. This chapter may have no questions yet.')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [groupId])

  const currentQuestion = questions[currentIndex]
  const isLast = currentIndex === questions.length - 1
  const selectedOption = responses[currentQuestion?.id]
  const answeredCount = Object.keys(responses).length
  const skippedCount = [...skipped].filter(id => !responses[id]).length

  const handleSelect = (option) => {
    setResponses(prev => ({ ...prev, [currentQuestion.id]: option }))
    setSkipped(prev => {
      const next = new Set(prev)
      next.delete(currentQuestion.id)
      return next
    })
  }

  const handleSkip = () => {
    setSkipped(prev => new Set([...prev, currentQuestion.id]))
    setCurrentIndex(i => i + 1)
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const responseList = questions
        .filter(q => responses[q.id])
        .map(q => ({
          question_id: q.id,
          selected: responses[q.id],
        }))
      await submitAttempt(attemptId, responseList)
      onComplete(attemptId)
    } catch {
      setError('Failed to submit. Please try again.')
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (error) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <p className="text-red-500 text-sm">{error}</p>
      <button onClick={onBack} className="text-gray-600 text-sm underline">Go back</button>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => {
              if (answeredCount === 0 && skippedCount === 0) {
                onBack()
                return
              }
              const parts = []
              if (answeredCount > 0) parts.push(`answered ${answeredCount}`)
              if (skippedCount > 0) parts.push(`skipped ${skippedCount}`)
              if (window.confirm(`You've ${parts.join(', ')} of ${questions.length} questions. Exit and lose your progress?`)) {
                onBack()
              }
            }}
            className="text-gray-500 text-sm hover:text-gray-700"
          >← Exit</button>
          <div className="flex flex-col items-end gap-0.5">
            <span className="text-sm text-gray-500">
              Question {currentIndex + 1} of {questions.length}
            </span>
            <span className="text-xs text-gray-400">
              {answeredCount} answered{skippedCount > 0 ? ` · ${skippedCount} skipped` : ''}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-8">
          <div
            className="bg-gray-900 h-1.5 rounded-full transition-all"
            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
          />
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
          <p className="text-gray-900 font-medium leading-relaxed whitespace-pre-line">
            {currentQuestion.question_text}
          </p>
        </div>

        <div className="flex flex-col gap-3 mb-8">
          {['a', 'b', 'c', 'd'].map((opt) => (
            <button
              key={opt}
              onClick={() => handleSelect(opt)}
              className={`text-left p-4 rounded-2xl border-2 transition-colors
                ${selectedOption === opt
                  ? 'border-gray-900 bg-gray-900 text-white'
                  : 'border-gray-200 bg-white text-gray-800 hover:border-gray-400'}`}
            >
              <span className="font-medium uppercase mr-3">{opt}.</span>
              {currentQuestion.options[opt]}
            </button>
          ))}
        </div>

        <div className="flex justify-between items-center">
          <button
            onClick={() => setCurrentIndex(i => i - 1)}
            disabled={currentIndex === 0}
            className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 disabled:opacity-30 hover:border-gray-400 transition-colors"
          >
            Previous
          </button>

          <div className="flex items-center gap-3">
            {!isLast && (
              <button
                onClick={handleSkip}
                className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-500 hover:border-gray-400 hover:text-gray-700 transition-colors"
              >
                Skip
              </button>
            )}

            {isLast ? (
              <button
                onClick={handleSubmit}
                disabled={submitting || answeredCount === 0}
                className="px-6 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-medium disabled:opacity-40 hover:bg-gray-700 transition-colors"
              >
                {submitting ? 'Submitting...' : 'Submit Quiz'}
              </button>
            ) : (
              <button
                onClick={() => setCurrentIndex(i => i + 1)}
                disabled={!selectedOption}
                className="px-5 py-2.5 rounded-xl bg-gray-900 text-white text-sm disabled:opacity-40 hover:bg-gray-700 transition-colors"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
