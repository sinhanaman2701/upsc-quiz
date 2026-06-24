import { useState, useEffect } from 'react'
import { getAttempt } from '../api/attempts'

export default function ResultsScreen({ attemptId, onRetry, onPickGroup }) {
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getAttempt(attemptId).then(setResult).catch(() => setError('Failed to load results.'))
  }, [attemptId])

  if (!result && !error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (error) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <p className="text-red-500 text-sm">{error}</p>
      <button onClick={onPickGroup} className="text-gray-600 text-sm underline">Go back</button>
    </div>
  )

  const pct = result.total > 0 ? Math.round((result.score / result.total) * 100) : 0

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center mb-8">
          <p className="text-5xl font-bold text-gray-900 mb-1">{result.score}/{result.total}</p>
          <p className="text-gray-500">{pct}% correct</p>
        </div>

        <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">Review</h2>

        <div className="flex flex-col gap-4 mb-8">
          {result.breakdown.map((item, i) => (
            <div key={item.question_id}
              className={`bg-white rounded-2xl border-2 p-5
                ${item.is_correct ? 'border-green-200' : 'border-red-200'}`}
            >
              <p className="text-gray-900 font-medium mb-3 text-sm">{i + 1}. {item.question_text}</p>

              <div className="flex flex-col gap-1.5 mb-3">
                {['a', 'b', 'c', 'd'].map(opt => (
                  <div key={opt}
                    className={`px-3 py-2 rounded-xl text-sm
                      ${opt === item.correct_answer ? 'bg-green-50 text-green-800 font-medium' : ''}
                      ${opt === item.selected && !item.is_correct ? 'bg-red-50 text-red-700 line-through' : ''}`}
                  >
                    <span className="uppercase font-medium mr-2">{opt}.</span>{item.options[opt]}
                  </div>
                ))}
              </div>

              {item.explanation && (
                <div className="bg-gray-50 rounded-xl p-3 text-sm text-gray-600 leading-relaxed">
                  <span className="font-medium text-gray-700">Explanation: </span>
                  {item.explanation}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button onClick={onRetry}
            className="flex-1 py-3 rounded-xl border border-gray-200 text-sm text-gray-700 hover:border-gray-400 transition-colors">
            Retry
          </button>
          <button onClick={onPickGroup}
            className="flex-1 py-3 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 transition-colors">
            Pick another chapter
          </button>
        </div>
      </div>
    </div>
  )
}
