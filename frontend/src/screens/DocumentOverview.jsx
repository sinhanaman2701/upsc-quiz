import { useState, useEffect } from 'react'
import { getDocument } from '../api/documents'
import { getGroups } from '../api/groups'

export default function DocumentOverview({ docId, onStartQuiz, onBack }) {
  const [document, setDocument] = useState(null)
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      const [doc, grps] = await Promise.all([getDocument(docId), getGroups(docId)])
      setDocument(doc)
      setGroups(grps)
      setLoading(false)
    }
    load()
  }, [docId])

  useEffect(() => {
    if (groups.length === 1 && groups[0].group_type === 'none') {
      onStartQuiz(groups[0].id)
    }
  }, [groups, onStartQuiz])

  const groupLabel = () => {
    if (!groups.length) return 'Groups'
    const types = [...new Set(groups.map(g => g.group_type))]
    if (types.includes('chapter')) return 'Chapters'
    if (types.includes('section')) return 'Sections'
    if (types.includes('part')) return 'Parts'
    return 'Topics'
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  // Single group with type "none" — useEffect will navigate away; render nothing
  if (groups.length === 1 && groups[0].group_type === 'none') return null

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <button onClick={onBack} className="text-gray-500 text-sm mb-6 hover:text-gray-700 flex items-center gap-1">
          ← Back
        </button>

        <h1 className="text-2xl font-semibold text-gray-900 mb-1">{document.filename}</h1>
        <p className="text-gray-500 text-sm mb-8">
          {document.total_questions} questions extracted
          {document.failed_questions > 0 && ` · ${document.failed_questions} could not be parsed`}
        </p>

        <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-3">
          Select a {groupLabel().slice(0, -1)}
        </h2>

        <div className="flex flex-col gap-3">
          {groups.map((group) => (
            <div key={group.id}
              className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center justify-between hover:border-gray-400 transition-colors"
            >
              <div>
                <p className="font-medium text-gray-900">{group.display_name}</p>
                <p className="text-sm text-gray-500 mt-0.5">{group.question_count} questions</p>
              </div>
              <button
                onClick={() => onStartQuiz(group.id)}
                className="bg-gray-900 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
              >
                Start Quiz
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
