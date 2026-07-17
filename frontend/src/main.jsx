import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowRight, Check, ChevronDown, FileText, Gauge, Lightbulb, RefreshCw, ShieldCheck, Sparkles, Target, UploadCloud } from 'lucide-react'
import './styles.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || 'careerpilot_access_token'

function Section({ eyebrow, title, children, className = '' }) {
  return <section className={`panel ${className}`}><div className="section-heading"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>{children}</section>
}

function List({ items = [], tone = '' }) {
  return <ul className={`clean-list ${tone}`}>{items.map((item, index) => <li key={`${item}-${index}`}><Check size={15} strokeWidth={3} /><span>{item}</span></li>)}</ul>
}

function CoachReply({ text }) {
  const lines = (text || '').replace(/\s+(?=\d+\.\s)/g, '\n').split(/\n+/).map(line => line.trim()).filter(Boolean)
  return <div className="coach-reply">
    {lines.map((line, index) => {
      const numbered = line.match(/^(\d+)\.\s+(.*)$/)
      const bullet = line.match(/^[-*]\s+(.*)$/)
      const content = (numbered?.[2] || bullet?.[1] || line).replace(/\*\*/g, '')
      if (numbered) return <div className="coach-numbered" key={`${line}-${index}`}><span>{numbered[1]}</span><p>{content}</p></div>
      if (bullet) return <div className="coach-bullet" key={`${line}-${index}`}><span /> <p>{content}</p></div>
      return <p className={/^[A-Z][^:]{1,60}:$/.test(content) ? 'coach-heading' : ''} key={`${line}-${index}`}>{content}</p>
    })}
  </div>
}

function UploadView({ token, user, history, onComplete, onLogout, onOpenReport }) {
  const [file, setFile] = useState(null)
  const [role, setRole] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [jobDescriptionFile, setJobDescriptionFile] = useState(null)
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
    setLoading(true)
    setStage(0)
    const timer = window.setInterval(() => setStage(value => Math.min(value + 1, 3)), 1800)
    try {
      const form = new FormData()
      form.append('resume', file)
      form.append('job_role', role.trim())
      if (jobDescription.trim()) form.append('job_description', jobDescription.trim())
      if (jobDescriptionFile) form.append('job_description_file', jobDescriptionFile)
      const response = await fetch(`${API_URL}/api/analyze-resume`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form })
      const body = await response.json()
      if (!response.ok) throw new Error(body.message || 'We could not analyze that resume.')
      onComplete(body.analysis, role.trim(), body.report_id)
    } catch (err) {
      setError(err.message || 'Connection lost. Please try again.')
    } finally {
      window.clearInterval(timer)
      setLoading(false)
    }
  }

  return <main className="page-shell">
    <div className="workspace-bar"><div><span className="eyebrow">CAREER WORKSPACE</span><strong>Welcome, {user.full_name}</strong></div><button className="ghost-button" onClick={onLogout}>Log out</button></div>
    <div className="intro-grid"><div><p className="eyebrow">PERSONALIZED CAREER INTELLIGENCE</p><h1>Bridge the gap between your resume and your <em>dream job.</em></h1><p className="lede">AI SkillBridge turns a resume and a target role into a clear, practical plan for becoming job-ready.</p><div className="proof-row"><span><ShieldCheck size={17} /> Private by design</span><span><Sparkles size={17} /> One focused analysis</span></div></div>
      <div className="upload-card"><div className="card-kicker"><span className="icon-badge"><UploadCloud size={20} /></span><span>Start your analysis</span></div><h2>Show us where you are.</h2><p className="muted">Upload a text-based PDF and tell us where you want to go.</p>
        <form onSubmit={submit}><label className={`drop-zone ${file ? 'has-file' : ''}`}><input type="file" accept="application/pdf,.pdf" onChange={event => setFile(event.target.files?.[0] || null)} /><FileText size={28} />{file ? <><strong>{file.name}</strong><small>Ready to analyze</small></> : <><strong>Drop your resume here</strong><small>or click to browse - PDF up to 10 MB</small></>}</label>
          <label className="field-label" htmlFor="role">Target job role</label><div className="input-wrap"><Target size={18} /><input id="role" value={role} onChange={event => setRole(event.target.value)} placeholder="e.g. Backend Developer" maxLength={120} /></div>
          <label className="field-label" htmlFor="job-description">Job description <span className="optional-label">optional</span></label><textarea id="job-description" className="jd-input" value={jobDescription} onChange={event => setJobDescription(event.target.value)} placeholder="Paste the employer job description for a more specific match..." rows="4" />
          <label className="jd-file-label"><input type="file" accept="application/pdf,.pdf,text/plain,.txt" onChange={event => setJobDescriptionFile(event.target.files?.[0] || null)} />{jobDescriptionFile ? `Attached: ${jobDescriptionFile.name}` : 'Or attach a JD as PDF or TXT'}</label>
          {error && <div className="error-message" role="alert">{error}</div>}<button className="primary-button" disabled={loading}>{loading ? <><span className="spinner" /> {stages[stage]}</> : <>Analyze my resume <ArrowRight size={18} /></>}</button>
        </form>
      </div>
    </div>
    <div className="feature-strip"><div><Gauge size={22} /><strong>ATS clarity</strong><span>Know how systems see you.</span></div><div><Target size={22} /><strong>Skill direction</strong><span>Focus on the gaps that matter.</span></div><div><Lightbulb size={22} /><strong>Next steps</strong><span>Leave with a plan, not a score.</span></div></div>
    <section className="workspace-history"><div className="section-heading"><span className="eyebrow">YOUR REPORTS</span><h2>Career Workspace</h2></div>{history.length ? history.map(item => <button className="history-item" key={item.id} onClick={() => onOpenReport(item.id)}><span><strong>{item.target_role}</strong><small>{item.resume_name}</small></span><b>{item.ats_score}%</b></button>) : <p className="muted">Your completed reports will appear here.</p>}</section>
  </main>
}

function Score({ score }) { return <div className="score-wrap"><div className="score-ring" style={{ '--score': `${score * 3.6}deg` }}><div><strong>{score}</strong><span>/ 100</span></div></div><div><span className="eyebrow">ATS COMPATIBILITY</span><p className="score-caption">A solid base with room to make your fit more visible.</p></div></div> }
function Roadmap({ roadmap }) { const [open, setOpen] = useState('week1'); return <div className="roadmap">{['week1', 'week2', 'week3', 'week4'].map((week, index) => <div className="roadmap-row" key={week}><button onClick={() => setOpen(open === week ? '' : week)}><span className="week-number">0{index + 1}</span><strong>Week {index + 1}</strong><ChevronDown size={18} /></button>{open === week && <div className="roadmap-content"><List items={roadmap?.[week]} /></div>}</div>)}</div> }

function CareerCoach({ token }) {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [reply, setReply] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  async function ask(event) {
    event.preventDefault(); if (!message.trim()) return; setLoading(true)
    try { const response = await fetch(`${API_URL}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ message, session_id: sessionId }) }); const body = await response.json(); if (response.ok) { setSessionId(body.session_id); setReply(body.message); setMessage('') } } finally { setLoading(false) }
  }
  return <><button className="coach-fab" onClick={() => setOpen(!open)}><Sparkles size={18} /> Coach</button>{open && <aside className="coach-panel"><div className="coach-panel-head"><div><span className="eyebrow">CAREER COACH</span><strong>Your context-aware mentor</strong></div><button className="text-button" onClick={() => setOpen(false)}>Close</button></div><div className="coach-suggestions"><button onClick={() => setMessage('Explain my skill gaps')}>Explain my skill gaps</button><button onClick={() => setMessage('Review my roadmap')}>Review my roadmap</button><button onClick={() => setMessage('Help me prepare for interviews')}>Interview prep</button></div><CoachReply text={reply || 'Ask about your resume, roadmap, job description, or interview preparation.'} /><form onSubmit={ask} className="coach-form"><input value={message} onChange={event => setMessage(event.target.value)} placeholder="Ask your career coach..." /><button className="primary-button" disabled={loading}>{loading ? '...' : 'Ask'}</button></form></aside>}</>
}

function Dashboard({ analysis, role, token, reportId, onReset }) {
  const [coverLetter, setCoverLetter] = useState('')
  const [coverLoading, setCoverLoading] = useState(false)
  const [coverError, setCoverError] = useState('')
  async function generateCoverLetter() {
    setCoverError(''); setCoverLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/generate-cover-letter`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ report_id: reportId }) })
      const body = await response.json(); if (!response.ok) throw new Error(body.message || 'Unable to generate cover letter.')
      setCoverLetter(body.cover_letter)
    } catch (err) { setCoverError(err.message) } finally { setCoverLoading(false) }
  }
  return <main className="dashboard"><div className="dashboard-top"><div><p className="eyebrow">YOUR CAREER REPORT - {role.toUpperCase()}</p><h1>Your next move, made clear.</h1><p className="lede">A practical read on where your resume stands and what will move it forward.</p></div><div className="dashboard-actions"><button className="ghost-button" onClick={generateCoverLetter}>Generate cover letter</button><button className="ghost-button" onClick={onReset}><RefreshCw size={16} /> Analyze another</button></div></div>
    <div className="kpi-grid"><Section eyebrow="01 / THE FIRST IMPRESSION" title="How good is my resume?"><Score score={analysis.ats_score} /><p className="reason">{analysis.ats_reason}</p></Section><Section eyebrow="02 / MATCH SIGNAL" title="Your skill snapshot"><div className="mini-stat"><span>Matched skills</span><strong>{analysis.matched_skills.length}</strong></div><div className="mini-stat accent"><span>Skills to build</span><strong>{analysis.missing_skills.length}</strong></div><div className="mini-stat"><span>Next 30 days</span><strong>4 weeks</strong></div></Section></div>
    <div className="two-col"><Section eyebrow="03 / WHAT IS WORKING" title="Strengths"><List items={analysis.strengths} /></Section><Section eyebrow="04 / WHAT IS HOLDING YOU BACK" title="Weaknesses"><List items={analysis.weaknesses} tone="warning" /></Section></div>
    <Section eyebrow="05 / THE GAP" title="Matched vs. missing skills"><div className="skill-columns"><div className="skill-block matched"><h3><span /> You already show</h3><div className="tag-list">{analysis.matched_skills.map(skill => <span key={skill}>{skill}</span>)}</div></div><div className="skill-block missing"><h3><span /> Build next</h3><div className="tag-list">{analysis.missing_skills.map(skill => <span key={skill}>{skill}</span>)}</div></div></div></Section>
    {analysis.job_match && <Section eyebrow="05B / JD MATCH" title="Resume vs Job Description Match"><div className="match-score-line"><strong>{analysis.job_match.overall_match_score}%</strong><span>semantic match score</span></div><div className="skill-columns"><div className="skill-block matched"><h3><span /> Matched requirements</h3><List items={analysis.job_match.skill_match} /></div><div className="skill-block missing"><h3><span /> Priority gaps</h3><List items={analysis.job_match.missing_skills} tone="warning" /></div></div><div className="match-details"><p><strong>Experience gap:</strong> {analysis.job_match.experience_gap}</p><p><strong>Education gap:</strong> {analysis.job_match.education_gap}</p></div><List items={analysis.job_match.recommended_improvements} /></Section>}
    <Section eyebrow="06 / RECRUITER SIMULATOR" title="Why might you be rejected?" className="rejection-panel"><div className="quote-mark">&quot;</div><p>{analysis.rejection_reason}</p><small>This is a simulation based on the resume and role you provided, not a verdict.</small></Section><Section eyebrow="07 / MAKE IT STRONGER" title="Resume bullet rewrite" className="rewrite-panel"><div className="rewrite-grid"><div><span className="rewrite-label before">BEFORE</span><p>{analysis.resume_rewrite.before}</p></div><div className="rewrite-arrow"><ArrowRight size={20} /></div><div><span className="rewrite-label after">AFTER</span><p>{analysis.resume_rewrite.after}</p></div></div></Section>
    <div className="two-col"><Section eyebrow="08 / YOUR PLAN" title="30-day learning roadmap"><Roadmap roadmap={analysis.learning_roadmap} /></Section><Section eyebrow="09 / PREPARE WITH INTENT" title="Interview questions"><List items={analysis.interview_questions} /></Section></div><Section eyebrow="10 / QUICK WINS" title="Resume improvements"><List items={analysis.resume_suggestions} /></Section><footer className="report-footer"><span><Sparkles size={16} /> Built to make career guidance more accessible.</span><button className="ghost-button" onClick={onReset}>Start another analysis <ArrowRight size={16} /></button></footer>
    {(coverLoading || coverError || coverLetter) && <div className="cover-modal" role="dialog" aria-label="Generated cover letter"><div className="cover-modal-card"><div className="section-heading"><span className="eyebrow">APPLICATION READY</span><h2>Your cover letter</h2></div>{coverLoading ? <p className="muted">Writing a role-specific letter...</p> : coverError ? <div className="error-message">{coverError}</div> : <><textarea className="cover-letter-output" value={coverLetter} readOnly /><button className="primary-button" onClick={() => navigator.clipboard?.writeText(coverLetter)}>Copy cover letter</button></>}<button className="text-button" onClick={() => { setCoverLetter(''); setCoverError('') }}>Close</button></div></div>}
    <CareerCoach token={token} />
  </main>
}

function AuthScreen({ onAuth }) { const [registerMode, setRegisterMode] = useState(false); const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false); async function submit(event) { event.preventDefault(); setError(''); setLoading(true); try { const endpoint = registerMode ? '/api/auth/register' : '/api/auth/login'; const payload = registerMode ? { full_name: name, email, password } : { email, password }; const response = await fetch(`${API_URL}${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); const body = await response.json(); if (!response.ok) throw new Error(body.message || 'Unable to authenticate.'); onAuth(body.access_token, body.user) } catch (err) { setError(err.message) } finally { setLoading(false) } } return <main className="auth-shell"><div className="auth-card"><span className="eyebrow">CAREERPILOT AI</span><h1>{registerMode ? 'Create your career workspace.' : 'Welcome back.'}</h1><p className="muted">{registerMode ? 'Keep your reports, plans, and progress in one private space.' : 'Continue building your path to job-readiness.'}</p><form onSubmit={submit}>{registerMode && <><label className="field-label" htmlFor="name">Full name</label><div className="input-wrap"><input id="name" value={name} onChange={event => setName(event.target.value)} placeholder="Your name" /></div></>}<label className="field-label" htmlFor="email">Email address</label><div className="input-wrap"><input id="email" type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" /></div><label className="field-label" htmlFor="password">Password</label><div className="input-wrap"><input id="password" type="password" value={password} onChange={event => setPassword(event.target.value)} placeholder="At least 8 characters" /></div>{error && <div className="error-message" role="alert">{error}</div>}<button className="primary-button" disabled={loading}>{loading ? 'Please wait...' : registerMode ? 'Create workspace' : 'Log in'}</button></form><button className="text-button" onClick={() => { setRegisterMode(!registerMode); setError('') }}>{registerMode ? 'Already have an account? Log in' : 'New here? Create an account'}</button></div></main> }

function App() { const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY)); const [user, setUser] = useState(null); const [report, setReport] = useState(null); const [role, setRole] = useState(''); const [reportId, setReportId] = useState(null); const [history, setHistory] = useState([]); useEffect(() => { if (!token) return; Promise.all([fetch(`${API_URL}/api/auth/profile`, { headers: { Authorization: `Bearer ${token}` } }), fetch(`${API_URL}/api/history`, { headers: { Authorization: `Bearer ${token}` } })]).then(async ([profileResponse, historyResponse]) => { if (!profileResponse.ok || !historyResponse.ok) throw new Error('Session expired'); setUser(await profileResponse.json()); setHistory(await historyResponse.json()) }).catch(() => { localStorage.removeItem(TOKEN_KEY); setToken(null); setUser(null) }) }, [token]); function authenticated(accessToken, profile) { localStorage.setItem(TOKEN_KEY, accessToken); setToken(accessToken); setUser(profile) } function logout() { localStorage.removeItem(TOKEN_KEY); setToken(null); setUser(null); setReport(null) } async function refreshHistory() { const response = await fetch(`${API_URL}/api/history`, { headers: { Authorization: `Bearer ${token}` } }); if (response.ok) setHistory(await response.json()) } async function openReport(id) { const response = await fetch(`${API_URL}/api/history/${id}`, { headers: { Authorization: `Bearer ${token}` } }); if (!response.ok) return; const body = await response.json(); setReport(body.analysis); setRole(body.target_role); setReportId(body.id) } if (!token || !user) return <AuthScreen onAuth={authenticated} />; if (report) return <Dashboard analysis={report} role={role} token={token} reportId={reportId} onReset={() => { setReport(null); setReportId(null); refreshHistory() }} />; return <UploadView token={token} user={user} history={history} onLogout={logout} onOpenReport={openReport} onComplete={(analysis, targetRole, savedReportId) => { setReport(analysis); setRole(targetRole); setReportId(savedReportId); refreshHistory() }} /> }

createRoot(document.getElementById('root')).render(<App />)
