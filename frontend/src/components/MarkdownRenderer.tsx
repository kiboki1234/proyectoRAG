import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-p:leading-relaxed prose-a:text-brand-600 prose-code:text-brand-700 prose-code:bg-brand-100 prose-code:px-1 prose-code:rounded prose-pre:bg-brand-100 prose-ul:my-2 prose-ol:my-2 prose-li:my-0">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
