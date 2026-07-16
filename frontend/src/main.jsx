import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowRight, Check, ChevronDown, FileText, Gauge, Lightbulb, RefreshCw, ShieldCheck, Sparkles, Target, UploadCloud } from 'lucide-react'
import './styles.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Section({ eyebrow, title, children, className = '' }) {
  return <section className={`panel ${className}`}><div className="section-heading"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>{children}</section>
}

function List({ items, tone = '' }) {
  return <ul className={`clean-list ${tone}`}>{items?.map((item, index) => <li key={`${item}-${index}`}><Check size={15} strokeWidth={3} /> <span>{item}</span></li>)}</ul>
}

function UploadView({ onComplete }) {
  const [file, setFile] = useState(null)
  const [role, setRole] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [stage, setStage] = useState(0)
  const stages = ['Extracting resume...', 'Understanding your profile...', 'Comparing with job requirements...', 'Preparing your career report...']

  async function submit(event) {
    event.preventDefault()
    setError('')
    if (!file) return setError('Please choose your resume PDF first.')
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) return setError('Only PDF files are supported.')
    if (!role.trim()) return setError('Please enter a target job role.')
    setLoading(true); setStage(0)
    const timer = window.setInterval(() => setStage(value => Math.min(value + 1, 3)), 1800)
    try {
      const form = new FormData(); form.append('resume', file); form.append('job_role', role.trim())
      const response = await fetch(`${API_URL}/api/analyze-resume`, { method: 'POST', body: form })
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail?.message || body.message || 'We could not analyze that resume.')
      onComplete(body.analysis, role.trim())
    } catch (err) { setError(err.message || 'Connection lost. Please try again.') } finally { window.clearInterval(timer); setLoading(false) }
  }

  return <main className="page-shell"><div className="intro-grid"><div><p className="eyebrow">PERSONALIZED CAREER INTELLIGENCE</p><h1>Bridge the gap between your resume and your <em>dream job.</em></h1><p className="lede">AI SkillBridge turns a resume and a target role into a clear, practical plan for becoming job-ready.</p><div className="proof-row"><span><ShieldCheck size={17} /> Private by design</span><span><Sparkles size={17} /> One focused analysis</span></div></div><div className="upload-card"><div className="card-kicker"><span className="icon-badge"><UploadCloud size={20} /></span><span>Start your analysis</span></div><h2>Show us where you are.</h2><p className="muted">Upload a text-based PDF and tell us where you want to go.</p><form onSubmit={submit}><label className={`drop-zone ${file ? 'has-file' : ''}`}><input type="file" accept="application/pdf,.pdf" onChange={event => setFile(event.target.files?.[0] || null)} /><FileText size={28} />{file ? <><strong>{file.name}</strong><small>Ready to analyze</small></> : <><strong>Drop your resume here</strong><small>or click to browse · PDF up to 10 MB</small></>}</label><label className="field-label" htmlFor="role">Target job role</label><div className="input-wrap"><Target size={18} /><input id="role" value={role} onChange={event => setRole(event.target.value)} placeholder="e.g. Backend Developer" maxLength={120} /></div>{error && <div className="error-message" role="alert">{error}</div>}<button className="primary-button" disabled={loading}>{loading ? <><span className="spinner" /> {stages[stage]}</> : <>Analyze my resume <ArrowRight size={18} /></>}</button></form></div></div><div className="feature-strip"><div><Gauge size={22} /><strong>ATS clarity</strong><span>Know how systems see you.</span></div><div><Target size={22} /><strong>Skill direction</strong><span>Focus on the gaps that matter.</span></div><div><Lightbulb size={22} /><strong>Next steps</strong><span>Leave with a plan, not a score.</span></div></div></main>
}

function Score({ score }) { return <div className="score-wrap"><div className="score-ring" style={{ '--score': `${score * 3.6}deg` }}><div><strong>{score}</strong><span>/ 100</span></div></div><div><span className="eyebrow">ATS COMPATIBILITY</span><p className="score-caption">A solid base with room to make your fit more visible.</p></div></div> }

function Roadmap({ roadmap }) { const [open, setOpen] = useState('week1'); return <div className="roadmap">{['week1','week2','week3','week4'].map((week, index) => <div className={`roadmap-row ${open === week ? 'open' : ''}`} key={week}><button onClick={() => setOpen(open === week ? '' : week)}><span className="week-number">0{index + 1}</span><strong>Week {index + 1}</strong><ChevronDown size={18} /></button>{open === week && <div className="roadmap-content"><List items={roadmap?.[week]} /></div>}</div>)}</div> }

function Dashboard({ analysis, role, onReset }) { return <main className="dashboard"><div className="dashboard-top"><div><p className="eyebrow">YOUR CAREER REPORT · {role.toUpperCase()}</p><h1>Your next move, made clear.</h1><p className="lede">A practical read on where your resume stands and what will move it forward.</p></div><button className="ghost-button" onClick={onReset}><RefreshCw size={16} /> Analyze another</button></div><div className="kpi-grid"><Section eyebrow="01 / THE FIRST IMPRESSION" title="How good is my resume?" className="score-panel"><Score score={analysis.ats_score} /><p className="reason">{analysis.ats_reason}</p></Section><Section eyebrow="02 / MATCH SIGNAL" title="Your skill snapshot" className="snapshot-panel"><div className="mini-stat"><span>Matched skills</span><strong>{analysis.matched_skills.length}</strong></div><div className="mini-stat accent"><span>Skills to build</span><strong>{analysis.missing_skills.length}</strong></div><div className="mini-stat"><span>Next 30 days</span><strong>4 weeks</strong></div></Section></div><div className="two-col"><Section eyebrow="03 / WHAT IS WORKING" title="Strengths"><List items={analysis.strengths} /></Section><Section eyebrow="04 / WHAT IS HOLDING YOU BACK" title="Weaknesses"><List items={analysis.weaknesses} tone="warning" /></Section></div><Section eyebrow="05 / THE GAP" title="Matched vs. missing skills"><div className="skill-columns"><div className="skill-block matched"><h3><span /> You already show</h3><div className="tag-list">{analysis.matched_skills.map(skill => <span key={skill}>{skill}</span>)}</div></div><div className="skill-block missing"><h3><span /> Build next</h3><div className="tag-list">{analysis.missing_skills.map(skill => <span key={skill}>{skill}</span>)}</div></div></div></Section><Section eyebrow="06 / RECRUITER SIMULATOR" title="Why might you be rejected?" className="rejection-panel"><div className="quote-mark">“</div><p>{analysis.rejection_reason}</p><small>This is a simulation based on the resume and role you provided, not a verdict.</small></Section><Section eyebrow="07 / MAKE IT STRONGER" title="Resume bullet rewrite" className="rewrite-panel"><div className="rewrite-grid"><div><span className="rewrite-label before">BEFORE</span><p>{analysis.resume_rewrite.before}</p></div><div className="rewrite-arrow"><ArrowRight size={20} /></div><div><span className="rewrite-label after">AFTER</span><p>{analysis.resume_rewrite.after}</p></div></div></Section><div className="two-col"><Section eyebrow="08 / YOUR PLAN" title="30-day learning roadmap"><Roadmap roadmap={analysis.learning_roadmap} /></Section><Section eyebrow="09 / PREPARE WITH INTENT" title="Interview questions"><List items={analysis.interview_questions} /></Section></div><Section eyebrow="10 / QUICK WINS" title="Resume improvements"><List items={analysis.resume_suggestions} /></Section><footer className="report-footer"><span><Sparkles size={16} /> Built to make career guidance more accessible.</span><button className="ghost-button" onClick={onReset}>Start another analysis <ArrowRight size={16} /></button></footer></main> }

function App() { const [report, setReport] = useState(null); const [role, setRole] = useState(''); return report ? <Dashboard analysis={report} role={role} onReset={() => setReport(null)} /> : <UploadView onComplete={(analysis, targetRole) => { setReport(analysis); setRole(targetRole) }} /> }

createRoot(document.getElementById('root')).render(<App />)

