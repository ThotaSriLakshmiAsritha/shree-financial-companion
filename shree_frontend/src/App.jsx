import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import {
  confirmTransactionProposal,
  createGoal,
  createTransactionProposal,
  distributeSavings,
  getGoalDetails,
  getCurrentUser,
  getFinancialContext,
  getGoals,
  getCurrentStory,
  getTransactions,
  narrateStory,
  transcribeBrowserVoice,
  sendConversationMessage,
  updateProfile,
  updatePreferredLanguage,
} from './api.js'
import { getAccessToken, supabase, supabaseConfigured } from './supabase.js'
import warliFooter from './assets/warli-footer.png'
import warliGoal from './assets/warli-goal.png'
import warliHero1 from './assets/warli-hero-1.png'
import warliHero2 from './assets/warli-hero-2.png'
import warliHero3 from './assets/warli-hero-3.png'
import warliHero4 from './assets/warli-hero-4.png'
import warliHero5 from './assets/warli-hero-5.png'
import {
  describeVoiceTransaction,
  isConfirmation,
  isRejection,
  mergeVoiceTransaction,
} from './voiceTransaction.js'

const languages = [
  { code: 'te', label: 'తెలుగు' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'en', label: 'English' },
]

const translations = {
  te: {
    language: 'తెలుగు', brand: 'శ్రీ', subtitle: 'మీ ఆర్థిక ప్రయాణంలో మీతో', user: 'మీరు', avatar: 'శ్రీ', languageLabel: 'భాష',
    heroEyebrow: 'మీ రోజువారీ తోడు', heroGreeting: 'నమస్కారం', heroTitle: <>నమస్కారం,<br /><em>మీకు స్వాగతం!</em></>, heroLead: 'మీ డబ్బు ప్రయాణం ఇక్కడ ఉంది.', heroNote: <>చిన్న చిన్న పొదుపులతో...<br />పెద్ద లక్ష్యాల వైపు.</>, carouselLabel: 'హీరో చిత్రాలు', slideAlt: 'వర్లీ కళా చిత్రం',
    monthEyebrow: 'ఈ నెల సంగతులు', snapshot: 'మీ ఆర్థిక చిత్రం', income: 'ఇటీవలి ఆదాయం', expenses: 'ఖర్చులు', monthlySavings: 'నెలవారీ పొదుపు', totalSavings: 'మొత్తం పొదుపు', thisMonth: 'ఈ నెల', soFar: 'ఇప్పటి వరకు',
    goalEyebrow: 'మీకు ముఖ్యమైనది', goalTitle: 'నా లక్ష్యం', goalName: 'కుట్టు మిషన్ కొనడం', progressLabel: 'కుట్టు మిషన్ లక్ష్యం 30 శాతం పూర్తయింది', milestone: 'తదుపరి మైలురాయికి', only: 'మాత్రమే.', continue: <>ముందుకు<br />సాగుదాం</>,
    actionEyebrow: 'మీతో మాట్లాడే సమయం', actionTitle: 'మీకు ఏది కావాలి?', callEyebrow: 'మీ ప్రశ్నలకు చోటు', callTitle: 'మాట్లాడండి', callCopy: <>మీ ప్రశ్నలు, లక్ష్యాలు, పొదుపులు —<br />మీ సహచరితో మాట్లాడండి.</>, callButton: 'ఇప్పుడే కాల్ చేయండి', voiceEyebrow: 'మీ మాటల్లోనే నమోదు', voiceTitle: 'వాయిస్ ద్వారా నమోదు చేయండి', voiceCopy: 'మీరు ఖర్చు చేసినది లేదా సంపాదించినది చెప్పండి.', speak: 'మాట్లాడండి', listening: 'వింటున్నాను', listeningTitle: 'చెప్పండి, వింటున్నాను...', listeningCopy: 'మీ ఖర్చు లేదా ఆదాయం గురించి చెప్పండి.', stop: 'ఆపండి', words: 'మీ మాటలు', transcription: 'ఈరోజు కూరగాయలకు ₹300 ఖర్చు చేశాను.', heard: 'మీరు చెప్పింది ఇదేనా?', doneListening: 'వినడం పూర్తి', confirm: 'నమోదు చేయనా?', vegetables: 'కూరగాయలు — ₹300', recordQuestion: 'ఖర్చు నమోదు చేయాలా?', confirmButton: 'అవును, నమోదు చేయండి', change: 'మార్చండి', finished: 'అయిపోయింది', success: '✓ ఖర్చు నమోదు అయింది', fresh: 'మీ రోజువారీ చిత్రం తాజాగా ఉంది.', another: 'మరోటి నమోదు చేయండి', manualEyebrow: 'మీ చేతితో నమోదు', manualTitle: 'మాన్యువల్ ఎంట్రీ', manualCopy: 'ఆదాయం లేదా ఖర్చును నమోదు చేయండి.', incomeOption: 'ఆదాయం', expenditureOption: 'ఖర్చు', amountLabel: 'మొత్తం', reasonLabel: 'కారణం', reasonPlaceholder: 'ఉదా: కూరగాయలు', submitEntry: 'ఎంట్రీని సమీక్షించండి', pendingEyebrow: 'నిర్ధారణ అవసరం', pendingTitle: 'ఈ ఎంట్రీని నమోదు చేయనా?', pendingCopy: 'మీరు చెప్పిన వివరాలను ఒకసారి పరిశీలించండి.', confirmEntry: 'అవును, నమోదు చేయండి', editEntry: 'మార్చండి', savedIncome: '✓ ఆదాయం నమోదు అయింది', savedExpense: '✓ ఖర్చు నమోదు అయింది', entryFresh: 'మీ ఆర్థిక చిత్రం తాజాగా ఉంది.', entryError: 'ఎంట్రీని పంపలేకపోయాం. దయచేసి మళ్లీ ప్రయత్నించండి.', confirmError: 'ఎంట్రీని నిర్ధారించలేకపోయాం. దయచేసి మళ్లీ ప్రయత్నించండి.',
    nextEyebrow: 'మీకోసం ఒక చిన్న గుర్తు', nextTitle: <>మీ తదుపరి అడుగు <span>🌱</span></>, goalLink: 'లక్ష్యాన్ని చూడండి',
    storyEyebrow: 'ఈరోజు చిన్న పాఠం', storyTitle: <>ఒక కథ విందామా? <span>🌾</span></>, storyCopy: 'ఒకసారి ఒక మహిళ కుట్టు మిషన్ కొనాలని అనుకుంది. ఆమె ముందు రెండు మార్గాలు ఉన్నాయి...', storyButton: 'కథ విందాం', footerAlt: 'గ్రామీణ జీవితం చూపించే వర్లీ కళ', footerCopy: 'మీ ఆర్థిక ప్రయాణంలో మీతో',
  },
  hi: {
    language: 'हिंदी', brand: 'श्री', subtitle: 'आपकी आर्थिक यात्रा में आपके साथ', user: 'आप', avatar: 'आ', languageLabel: 'भाषा',
    heroEyebrow: 'आपका रोज़ का साथी', heroGreeting: 'नमस्ते', heroTitle: <>नमस्ते,<br /><em>आपका स्वागत है!</em></>, heroLead: 'आपकी पैसों की यात्रा यहाँ है।', heroNote: <>छोटी-छोटी बचत से...<br />बड़े लक्ष्यों की ओर।</>, carouselLabel: 'मुख्य चित्र', slideAlt: 'वरली कला चित्र',
    monthEyebrow: 'इस महीने का हाल', snapshot: 'आपकी आर्थिक तस्वीर', income: 'हाल की आमदनी', expenses: 'खर्च', monthlySavings: 'मासिक बचत', totalSavings: 'कुल बचत', thisMonth: 'इस महीने', soFar: 'अब तक',
    goalEyebrow: 'आपके लिए ज़रूरी', goalTitle: 'मेरा लक्ष्य', goalName: 'सिलाई मशीन खरीदना', progressLabel: 'सिलाई मशीन का लक्ष्य 30 प्रतिशत पूरा', milestone: 'अगले पड़ाव तक', only: 'ही बाकी।', continue: <>आगे<br />बढ़ते हैं</>,
    actionEyebrow: 'आपसे बात करने का समय', actionTitle: 'आपको क्या चाहिए?', callEyebrow: 'आपके सवालों के लिए जगह', callTitle: 'बात करें', callCopy: <>अपने सवाल, लक्ष्य और बचत —<br />अपने साथी से साझा करें।</>, callButton: 'अभी कॉल करें', voiceEyebrow: 'अपनी आवाज़ में दर्ज करें', voiceTitle: 'आवाज़ से दर्ज करें', voiceCopy: 'आपने जो खर्च किया या कमाया, वह बताएं।', speak: 'बात करें', listening: 'सुन रही हूँ', listeningTitle: 'बताइए, मैं सुन रही हूँ...', listeningCopy: 'अपने खर्च या आमदनी के बारे में बताएं।', stop: 'रोकें', words: 'आपकी बात', transcription: 'आज सब्ज़ियों पर ₹300 खर्च किए।', heard: 'क्या आपने यही कहा?', doneListening: 'सुनना पूरा करें', confirm: 'दर्ज करूँ?', vegetables: 'सब्ज़ियाँ — ₹300', recordQuestion: 'खर्च दर्ज करें?', confirmButton: 'हाँ, दर्ज करें', change: 'बदलें', finished: 'हो गया', success: '✓ खर्च दर्ज हो गया', fresh: 'आपकी रोज़ की तस्वीर अपडेट है।', another: 'एक और दर्ज करें', manualEyebrow: 'अपने हाथ से दर्ज करें', manualTitle: 'मैन्युअल एंट्री', manualCopy: 'अपनी आमदनी या खर्च दर्ज करें।', incomeOption: 'आमदनी', expenditureOption: 'खर्च', amountLabel: 'राशि', reasonLabel: 'कारण', reasonPlaceholder: 'जैसे: सब्ज़ियाँ', submitEntry: 'एंट्री देखें', pendingEyebrow: 'पुष्टि ज़रूरी है', pendingTitle: 'क्या यह एंट्री दर्ज करें?', pendingCopy: 'दर्ज करने से पहले विवरण जाँच लें।', confirmEntry: 'हाँ, दर्ज करें', editEntry: 'बदलें', savedIncome: '✓ आमदनी दर्ज हो गई', savedExpense: '✓ खर्च दर्ज हो गया', entryFresh: 'आपकी आर्थिक तस्वीर अपडेट है।', entryError: 'एंट्री भेजी नहीं जा सकी। फिर कोशिश करें।', confirmError: 'एंट्री की पुष्टि नहीं हो सकी। फिर कोशिश करें।',
    nextEyebrow: 'आपके लिए एक छोटी याद', nextTitle: <>आपका अगला कदम <span>🌱</span></>, goalLink: 'लक्ष्य देखें',
    storyEyebrow: 'आज की छोटी सीख', storyTitle: <>एक कहानी सुनें? <span>🌾</span></>, storyCopy: 'एक बार एक महिला सिलाई मशीन खरीदना चाहती थी। उसके सामने दो रास्ते थे...', storyButton: 'कहानी सुनें', footerAlt: 'गाँव का जीवन दिखाती वरली कला', footerCopy: 'आपकी आर्थिक यात्रा में आपके साथ',
  },
  en: {
    language: 'English', brand: 'Shree', subtitle: 'With you on your financial journey', user: 'You', avatar: 'Y', languageLabel: 'Language',
    heroEyebrow: 'Your everyday companion', heroGreeting: 'Hello', heroTitle: <>Hello,<br /><em>Welcome!</em></>, heroLead: 'Your money journey is here.', heroNote: <>With small savings...<br />towards bigger goals.</>, carouselLabel: 'Hero artwork', slideAlt: 'Warli artwork',
    monthEyebrow: 'This month so far', snapshot: 'Your financial picture', income: 'Recent income', expenses: 'Expenses', monthlySavings: 'Monthly savings', totalSavings: 'Total savings', thisMonth: 'This month', soFar: 'So far',
    goalEyebrow: 'What matters to you', goalTitle: 'My goal', goalName: 'Buy a sewing machine', progressLabel: 'Sewing machine goal is 30 percent complete', milestone: 'Only', only: 'to the next milestone.', continue: <>Let’s<br />keep going</>,
    actionEyebrow: 'A moment to talk', actionTitle: 'What do you need?', callEyebrow: 'A place for your questions', callTitle: 'Talk', callCopy: <>Your questions, goals and savings —<br />talk with your companion.</>, callButton: 'Call now', voiceEyebrow: 'Record in your own words', voiceTitle: 'Record by voice', voiceCopy: 'Tell us what you spent or earned.', speak: 'Talk', listening: 'Listening', listeningTitle: 'Go ahead, I’m listening...', listeningCopy: 'Tell us about your spending or income.', stop: 'Stop', words: 'Your words', transcription: 'I spent ₹300 on vegetables today.', heard: 'Is this what you said?', doneListening: 'Finish listening', confirm: 'Record this?', vegetables: 'Vegetables — ₹300', recordQuestion: 'Record this expense?', confirmButton: 'Yes, record it', change: 'Change', finished: 'Done', success: '✓ Expense recorded', fresh: 'Your daily picture is up to date.', another: 'Record another', manualEyebrow: 'Enter it yourself', manualTitle: 'Manual entry', manualCopy: 'Record income or an expense in a few steps.', incomeOption: 'Income', expenditureOption: 'Expenditure', amountLabel: 'Amount', reasonLabel: 'Reason', reasonPlaceholder: 'e.g. Vegetables', submitEntry: 'Review entry', pendingEyebrow: 'Confirmation needed', pendingTitle: 'Record this entry?', pendingCopy: 'Please check the details before saving them.', confirmEntry: 'Yes, record it', editEntry: 'Change', savedIncome: '✓ Income recorded', savedExpense: '✓ Expense recorded', entryFresh: 'Your financial picture is up to date.', entryError: 'We could not send the entry. Please try again.', confirmError: 'We could not confirm the entry. Please try again.',
    nextEyebrow: 'A small note for you', nextTitle: <>Your next step <span>🌱</span></>, goalLink: 'View goal',
    storyEyebrow: 'A small lesson for today', storyTitle: <>Shall we hear a story? <span>🌾</span></>, storyCopy: 'Once, a woman wanted to buy a sewing machine. She had two paths in front of her...', storyButton: 'Hear the story', footerAlt: 'Warli art showing village life', footerCopy: 'With you on your financial journey',
  },
}

const slides = [warliHero1, warliHero2, warliHero3, warliHero4, warliHero5]
const companionPhoneNumber = '+9140455903507'
const dynamicNextStepCopy = {
  te: ({ savings, remaining, goalName, hasGoal }) => hasGoal
    ? <>ఈ నెల మీరు <strong>{formatMoney(savings)}</strong> పొదుపు చేశారు.<br />మీ {goalName} లక్ష్యానికి <strong>మరో {formatMoney(remaining)}</strong> దూరంలో ఉన్నారు.</>
    : <>మీ పొదుపు మరియు లక్ష్య పురోగతి ఇక్కడ కనిపిస్తుంది. మీ మొదటి లక్ష్యాన్ని సృష్టించండి.</>,
  hi: ({ savings, remaining, goalName, hasGoal }) => hasGoal
    ? <>इस महीने आपने <strong>{formatMoney(savings)}</strong> बचाए हैं।<br />आपके <strong>{goalName}</strong> लक्ष्य के लिए <strong>{formatMoney(remaining)}</strong> बाकी हैं।</>
    : <>आपकी बचत और लक्ष्य की प्रगति यहाँ दिखाई देगी। अपना पहला लक्ष्य बनाइए।</>,
  en: ({ savings, remaining, goalName, hasGoal }) => hasGoal
    ? <>You saved <strong>{formatMoney(savings)}</strong> this month.<br />You need <strong>{formatMoney(remaining)}</strong> more for your <strong>{goalName}</strong> goal.</>
    : <>Your savings and goal progress will appear here. Create your first goal to get started.</>,
}
function ChevronIcon() {
  return <svg className="language-chevron" viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1.5 L6 6.5 L11 1.5" /></svg>
}

function FinancialIcon({ type }) {
  const paths = {
    income: <><path d="M8 14V4" /><path d="m4.5 7.5 3.5-3.5 3.5 3.5" /><path d="M3 14h10" /></>,
    expenses: <><path d="M8 2v10" /><path d="m4.5 8.5 3.5 3.5 3.5-3.5" /><path d="M3 2h10" /></>,
    savings: <><circle cx="8" cy="8" r="5.5" /><path d="M8 5v6M5 8h6" /></>,
    wallet: <><path d="M3 5.5h9.5A1.5 1.5 0 0 1 14 7v5.5A1.5 1.5 0 0 1 12.5 14h-9A1.5 1.5 0 0 1 2 12.5v-7A1.5 1.5 0 0 1 3.5 4H12" /><path d="M10 9h4" /><circle cx="10" cy="9" r=".6" /></>,
  }
  return <svg className="financial-icon" viewBox="0 0 16 16" aria-hidden="true">{paths[type]}</svg>
}

function Header({ t, language, setLanguage, onSignOut }) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef(null)
  useEffect(() => {
    const closeOnOutside = (event) => { if (menuRef.current && !menuRef.current.contains(event.target)) setIsOpen(false) }
    const closeOnEscape = (event) => { if (event.key === 'Escape') setIsOpen(false) }
    document.addEventListener('mousedown', closeOnOutside)
    document.addEventListener('keydown', closeOnEscape)
    return () => { document.removeEventListener('mousedown', closeOnOutside); document.removeEventListener('keydown', closeOnEscape) }
  }, [])
  const chooseLanguage = (code) => { setLanguage(code); setIsOpen(false) }
  return <header className="site-header"><a className="brand" href="#top" aria-label={`${t.brand} ${t.subtitle}`}><span className="brand-mark">{t.brand}</span><span className="brand-subtitle">{t.subtitle}</span></a><div className="header-user"><div className="language-menu" ref={menuRef}><button className="language-picker" type="button" aria-label={`${t.languageLabel}: ${t.language}`} aria-haspopup="listbox" aria-expanded={isOpen} onClick={() => setIsOpen((open) => !open)}><span className="language-control"><span className="language-label">{t.language}</span><ChevronIcon /></span></button>{isOpen && <div className="language-dropdown" role="listbox" aria-label={t.languageLabel}>{languages.map((option) => <button className={language === option.code ? 'is-selected' : ''} key={option.code} type="button" role="option" aria-selected={language === option.code} onClick={() => chooseLanguage(option.code)}>{option.label}<span aria-hidden="true">{language === option.code ? '✓' : ''}</span></button>)}</div>}</div><span className="user-name">{t.user}</span><span className="user-avatar" aria-hidden="true">{t.avatar}</span>{onSignOut && <button className="text-button header-signout" type="button" onClick={onSignOut}>{t.signOut}</button>}</div></header>
}

function WarliArt({ image, alt, className = '' }) { return <img className={`warli-image ${className}`} src={image} alt={alt} /> }

function Hero({ t, userName }) {
  const [activeSlide, setActiveSlide] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  useEffect(() => { if (isPaused) return undefined; const timer = window.setInterval(() => setActiveSlide((current) => (current + 1) % slides.length), 5500); return () => window.clearInterval(timer) }, [isPaused])
  const selectSlide = (index) => { setActiveSlide(index); setIsPaused(true) }
  return <section className="hero section-shell" id="top"><div className="hero-copy"><p className="eyebrow">{t.heroEyebrow} <span>✦</span></p><h1>{t.heroGreeting},<br /><em>{userName || t.user}!</em></h1><p className="hero-lede">{t.heroLead}</p><p className="hero-note">{t.heroNote}</p><div className="hero-rule" aria-hidden="true"><span /><span /><span /></div></div><div className="hero-art-wrap"><div className="hero-art-frame">{slides.map((image, index) => <div className={`slide slide-${index + 1} ${activeSlide === index ? 'is-active' : ''}`} key={image}><WarliArt image={image} alt={`${t.slideAlt} ${index + 1}`} /></div>)}</div><div className="carousel-dots" role="group" aria-label={t.carouselLabel}>{slides.map((image, index) => <button key={image} className={activeSlide === index ? 'is-active' : ''} onClick={() => selectSlide(index)} aria-label={`${index + 1}`} aria-pressed={activeSlide === index} type="button" />)}</div></div></section>
}

function FinancialCard({ item, t }) { return <article className="financial-card"><div className="card-icon"><FinancialIcon type={item.icon} /></div><strong>{item.amount}</strong><p>{t[item.key]}</p><span>{t[item.note]}</span></article> }
function formatMoney(value) {
  const number = Number(value ?? 0)
  return `₹${new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(Number.isFinite(number) ? number : 0)}`
}

function localTransactionDate() {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
  return `${parts.find((part) => part.type === 'year')?.value}-${parts.find((part) => part.type === 'month')?.value}-${parts.find((part) => part.type === 'day')?.value}`
}

function calculateMonthlySavings(transactions) {
  const currentMonth = localTransactionDate().slice(0, 7)
  return transactions.reduce((total, transaction) => {
    if (!String(transaction.date || '').startsWith(currentMonth)) return total
    const amount = Number(transaction.amount ?? 0)
    if (!Number.isFinite(amount)) return total
    if (transaction.transaction_type === 'income' || transaction.transaction_type === 'saving') return total + amount
    if (transaction.transaction_type === 'expense') return total - amount
    return total
  }, 0)
}

function FinancialSnapshot({ t, financialContext }) {
  const monthlySavings = Number(financialContext?.total_income ?? 0) - Number(financialContext?.total_expenses ?? 0)
  const liveFinances = [
    { key: 'income', amount: formatMoney(financialContext?.total_income), note: 'thisMonth', icon: 'income' },
    { key: 'expenses', amount: formatMoney(financialContext?.total_expenses), note: 'thisMonth', icon: 'expenses' },
    { key: 'monthlySavings', amount: formatMoney(monthlySavings), note: 'thisMonth', icon: 'savings' },
    { key: 'totalSavings', amount: formatMoney(financialContext?.current_savings), note: 'soFar', icon: 'wallet' },
  ]
  return <section className="section-shell snapshot-section" aria-labelledby="snapshot-title"><div className="section-heading"><p className="eyebrow">{t.monthEyebrow}</p><h2 id="snapshot-title">{t.snapshot}</h2></div><div className="financial-grid">{liveFinances.map((item) => <FinancialCard item={item} t={t} key={item.key} />)}</div></section>
}

const goalCategories = [
  ['business', '✦'], ['education', '▣'], ['home', '⌂'], ['farming', '♧'], ['livestock', '♢'], ['marriage', '♡'], ['emergency', '＋'], ['general', '○'], ['other', '•'],
]

function defaultMilestones(target) {
  return [0.25, 0.5, 0.75, 1].map((ratio, index) => ({
    amount: target * ratio,
    is_completed: false,
    title: ['milestone25', 'milestone50', 'milestone75', 'milestone100'][index],
  }))
}

function goalMilestones(goal) {
  return goal?.milestones?.length ? goal.milestones : defaultMilestones(Number(goal?.target_amount ?? 0))
}

function GoalModal({ t, title, onClose, children }) {
  return <div className="goal-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><section className="goal-modal" role="dialog" aria-modal="true" aria-labelledby="goal-modal-title"><div className="goal-modal-heading"><h2 id="goal-modal-title">{title}</h2><button className="text-button" type="button" onClick={onClose} aria-label={t.cancel}>×</button></div>{children}</section></div>
}

function GoalForm({ t, onCreated, onClose }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [targetAmount, setTargetAmount] = useState('')
  const [category, setCategory] = useState('general')
  const [icon, setIcon] = useState('○')
  const [targetDate, setTargetDate] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    const target = Number(targetAmount)
    if (!name.trim() || !Number.isFinite(target) || target <= 0) { setError(t.entryError); return }
    setBusy(true)
    setError('')
    try {
      const created = await createGoal({ name: name.trim(), description: description.trim() || null, category, icon, target_amount: target, target_date: targetDate || null, currency: 'INR', status: 'active' }, await getAccessToken())
      onCreated?.(created)
      onClose()
    } catch (requestError) {
      setError(requestError?.message || t.entryError)
    } finally {
      setBusy(false)
    }
  }

  return <form className="goal-form goal-modal-form" onSubmit={submit}><label className="manual-field" htmlFor="goal-name"><span>{t.goalNameField}</span><input id="goal-name" value={name} onChange={(event) => setName(event.target.value)} placeholder={t.goalNameField} required /></label><label className="manual-field" htmlFor="goal-target"><span>{t.goalTargetField}</span><div className="amount-input"><span aria-hidden="true">₹</span><input id="goal-target" type="number" min="1" step="0.01" value={targetAmount} onChange={(event) => setTargetAmount(event.target.value)} placeholder={t.goalTargetHint} required /></div></label><label className="manual-field" htmlFor="goal-category"><span>{t.categoryLabel}</span><select id="goal-category" value={category} onChange={(event) => setCategory(event.target.value)}>{goalCategories.map(([value]) => <option key={value} value={value}>{t[value]}</option>)}</select></label><label className="manual-field" htmlFor="goal-description"><span>{t.descriptionLabel} <small>({t.optional})</small></span><textarea id="goal-description" rows="2" maxLength="500" value={description} onChange={(event) => setDescription(event.target.value)} placeholder={t.descriptionPlaceholder} /></label><label className="manual-field" htmlFor="goal-target-date"><span>{t.targetDateLabel} <small>({t.optional})</small></span><input id="goal-target-date" type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} /></label><fieldset className="goal-icon-fieldset"><legend>{t.iconLabel}</legend><div className="goal-icon-options">{goalCategories.slice(0, 8).map(([value, valueIcon]) => <label className={icon === valueIcon ? 'goal-icon-option is-selected' : 'goal-icon-option'} key={value}><input type="radio" name="goal-icon" value={valueIcon} checked={icon === valueIcon} onChange={() => setIcon(valueIcon)} /><span aria-hidden="true">{valueIcon}</span><small>{t[value]}</small></label>)}</div></fieldset>{error && <p className="manual-error" role="alert">{error}</p>}<div className="goal-modal-actions"><button className="text-button" type="button" onClick={onClose}>{t.cancel}</button><button className="action-button terracotta-button" type="submit" disabled={busy}>{busy ? '…' : t.createGoal}</button></div></form>
}

function GoalCard({ t, goal, onOpen, onAddMoney }) {
  const current = Number(goal.current_amount ?? 0)
  const target = Number(goal.target_amount ?? 0)
  const progress = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0
  const nextMilestone = goalMilestones(goal).find((milestone) => Number(milestone.amount) > current)
  const remaining = Math.max(Number(nextMilestone?.amount ?? target) - current, 0)
  const completed = goal.status === 'completed' || progress >= 100
  return <article className={`goal-card ${completed ? 'is-completed' : ''}`}><button className="goal-card-main" type="button" onClick={() => onOpen(goal)}><span className="goal-card-icon" aria-hidden="true">{goal.icon || '✦'}</span><span className="goal-card-heading"><strong>{goal.name}</strong><span>{goal.category ? t[goal.category] || goal.category : ''}</span></span><span className="goal-card-amount"><strong>{formatMoney(current)}</strong><span>{t.goalOf} {formatMoney(target)}</span><b>{progress}%</b></span><span className="progress-track" role="progressbar" aria-label={`${goal.name} ${progress}%`} aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100"><span style={{ width: `${progress}%` }} /></span><span className="goal-next"><span>✦</span> {completed ? t.goalAchieved : t.nextMilestone} <strong>{completed ? '' : `${formatMoney(remaining)} ${t.remaining}`}</strong></span></button>{!completed && <button className="action-button terracotta-button goal-add-button" type="button" onClick={() => onAddMoney(goal)}>+ {t.addMoney}</button>}</article>
}

function ContributionForm({ t, goal, onSaved, onClose }) {
  const current = Number(goal.current_amount ?? 0)
  const target = Number(goal.target_amount ?? 0)
  const remaining = Math.max(target - current, 0)
  const nextMilestone = goalMilestones(goal).find((milestone) => Number(milestone.amount) > current)
  const nextAmount = nextMilestone ? Number(nextMilestone.amount) : target
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const numericAmount = Number(amount || 0)
  const afterSaving = current + numericAmount

  const submit = async (event) => {
    event.preventDefault()
    if (!Number.isFinite(numericAmount) || numericAmount <= 0 || numericAmount > remaining) { setError(t.contributionError); return }
    setBusy(true)
    setError('')
    try {
      const token = await getAccessToken()
      const proposal = await createTransactionProposal({ transaction_type: 'saving', amount: numericAmount, currency: goal.currency || 'INR', category: 'goal_saving', description: `Saved for ${goal.name}`, date: localTransactionDate(), source: 'web', confidence: 1, raw_statement: `Saved ${numericAmount} for ${goal.name}`, goal_id: goal.id }, token)
      await confirmTransactionProposal(proposal.id, token)
      onSaved?.()
      onClose()
    } catch (requestError) {
      setError(requestError?.message || t.contributionError)
    } finally {
      setBusy(false)
    }
  }

  return <form className="goal-form goal-modal-form" onSubmit={submit}><p className="goal-modal-context">{goal.name}</p><p className="goal-modal-value">{t.currentSaved}: <strong>{formatMoney(current)}</strong></p><label className="manual-field" htmlFor="contribution-amount"><span>{t.saveAmount}</span><div className="amount-input"><span aria-hidden="true">₹</span><input id="contribution-amount" type="number" min="0.01" max={remaining} step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required /></div></label><div className="goal-save-preview"><span>{t.afterSaving}</span><strong>{formatMoney(afterSaving)}</strong><span>{t.nextMilestone}: {formatMoney(nextAmount)}</span></div>{error && <p className="manual-error" role="alert">{error}</p>}<div className="goal-modal-actions"><button className="text-button" type="button" onClick={onClose}>{t.cancel}</button><button className="action-button terracotta-button" type="submit" disabled={busy || remaining <= 0}>{busy ? '…' : `${t.addMoney} ${amount ? formatMoney(numericAmount) : ''}`}</button></div></form>
}

function SavingsDistributionForm({ t, goals, onSaved, onClose }) {
  const [amount, setAmount] = useState('')
  const [allocations, setAllocations] = useState(() => Object.fromEntries(goals.map((goal) => [goal.id, ''])))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const numericAmount = Number(amount || 0)
  const totalAllocated = Object.values(allocations).reduce((total, value) => total + Number(value || 0), 0)
  const matches = Number.isFinite(numericAmount) && numericAmount > 0 && Math.abs(totalAllocated - numericAmount) < 0.005
  const updateAllocation = (goalId, value) => setAllocations((current) => ({ ...current, [goalId]: value }))

  const submit = async (event) => {
    event.preventDefault()
    if (!matches) { setError(t.allocationMismatch); return }
    setBusy(true)
    setError('')
    try {
      await distributeSavings({ amount: numericAmount, allocations: goals.map((goal) => ({ goal_id: goal.id, amount: Number(allocations[goal.id] || 0) })) }, await getAccessToken())
      onSaved?.()
      onClose()
    } catch (requestError) {
      setError(requestError?.message || t.contributionError)
    } finally {
      setBusy(false)
    }
  }

  return <form className="goal-form goal-modal-form" onSubmit={submit}><label className="manual-field" htmlFor="savings-amount"><span>{t.todaySavings}</span><div className="amount-input"><span aria-hidden="true">₹</span><input id="savings-amount" type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required /></div></label><p className="goal-modal-context">{t.allocatePrompt}</p><div className="allocation-list">{goals.map((goal) => <label className="allocation-row" key={goal.id}><span><strong>{goal.name}</strong><small>{formatMoney(Math.max(Number(goal.target_amount) - Number(goal.current_amount), 0))} {t.remaining}</small></span><div className="amount-input"><span aria-hidden="true">₹</span><input type="number" min="0" step="0.01" max={Math.max(Number(goal.target_amount) - Number(goal.current_amount), 0)} value={allocations[goal.id] || ''} onChange={(event) => updateAllocation(goal.id, event.target.value)} aria-label={`${goal.name} ${t.addMoney}`} /></div></label>)}</div><div className="allocation-total"><span>{t.allocationTotal}</span><strong>{formatMoney(totalAllocated)}</strong><span>/ {formatMoney(numericAmount)}</span></div>{error && <p className="manual-error" role="alert">{error}</p>}<div className="goal-modal-actions"><button className="text-button" type="button" onClick={onClose}>{t.cancel}</button><button className="action-button terracotta-button" type="submit" disabled={busy || !matches}>{busy ? '…' : t.saveMoney}</button></div></form>
}

function GoalsSection({ t, goals, onGoalsChanged, onOpenGoal }) {
  const [showCreate, setShowCreate] = useState(false)
  const [showDistribution, setShowDistribution] = useState(false)
  const [contributionGoal, setContributionGoal] = useState(null)
  const activeGoals = goals.filter((goal) => goal.status === 'active')
  const completedGoals = goals.filter((goal) => goal.status === 'completed')
  return <section className="section-shell goals-section" id="goal-title" aria-labelledby="goals-title"><div className="goals-heading"><div><p className="eyebrow">{t.goalEyebrow}</p><h2 id="goals-title">{t.goalsTitle}</h2></div><div className="goals-actions"><button className="action-button terracotta-button" type="button" onClick={() => setShowCreate(true)}>+ {t.addGoal}</button>{activeGoals.length > 0 && <button className="action-button green-button" type="button" onClick={() => setShowDistribution(true)}>{t.saveMoney}</button>}</div></div>{activeGoals.length > 0 && <><h3 className="goals-subtitle">{t.activeGoals}</h3><div className="goals-grid">{activeGoals.map((goal) => <GoalCard key={goal.id} t={t} goal={goal} onOpen={onOpenGoal} onAddMoney={setContributionGoal} />)}</div></>}{activeGoals.length === 0 && <div className="goals-empty"><p>{t.noGoals}</p><span>{t.createFirstGoal}</span><button className="action-button terracotta-button" type="button" onClick={() => setShowCreate(true)}>+ {t.addGoal}</button></div>}{completedGoals.length > 0 && <><h3 className="goals-subtitle completed-heading">{t.completedGoals}</h3><div className="goals-grid">{completedGoals.map((goal) => <GoalCard key={goal.id} t={t} goal={goal} onOpen={onOpenGoal} onAddMoney={setContributionGoal} />)}</div></>}{showCreate && <GoalModal t={t} title={t.addGoal} onClose={() => setShowCreate(false)}><GoalForm t={t} onCreated={onGoalsChanged} onClose={() => setShowCreate(false)} /></GoalModal>}{showDistribution && <GoalModal t={t} title={t.saveMoney} onClose={() => setShowDistribution(false)}><SavingsDistributionForm t={t} goals={activeGoals} onSaved={onGoalsChanged} onClose={() => setShowDistribution(false)} /></GoalModal>}{contributionGoal && <GoalModal t={t} title={`${t.addMoney} — ${contributionGoal.name}`} onClose={() => setContributionGoal(null)}><ContributionForm t={t} goal={contributionGoal} onSaved={onGoalsChanged} onClose={() => setContributionGoal(null)} /></GoalModal>}</section>
}

function formatContributionDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short' }).format(date)
}

function GoalDetailsPage({ t, goal, onBack, onSaved }) {
  const [details, setDetails] = useState(goal)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showContribution, setShowContribution] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    void getAccessToken().then((token) => getGoalDetails(goal.id, token)).then((result) => {
      if (active) setDetails(result)
    }).catch((requestError) => {
      if (active) setError(requestError?.message || t.goalLoadError)
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [goal.id, t.goalLoadError])

  const current = Number(details?.current_amount ?? 0)
  const target = Number(details?.target_amount ?? 0)
  const progress = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0
  const milestones = goalMilestones(details)
  const nextMilestone = milestones.find((milestone) => Number(milestone.amount) > current)
  const remaining = Math.max(Number(nextMilestone?.amount ?? target) - current, 0)
  const reloadDetails = async () => {
    const result = await getGoalDetails(goal.id, await getAccessToken())
    setDetails(result)
    onSaved?.()
  }

  if (loading) return <main className="loading-page"><p>{t.loading}</p></main>
  if (error) return <main className="loading-page"><p className="manual-error" role="alert">{error}</p><button className="action-button terracotta-button" type="button" onClick={onBack}>{t.back}</button></main>

  return <section className="section-shell goal-details-page" aria-labelledby="goal-details-title"><button className="text-button goal-back-button" type="button" onClick={onBack}>← {t.back}</button><div className="goal-details-hero"><div><p className="eyebrow">{details.category ? t[details.category] || details.category : t.goalsTitle}</p><h2 id="goal-details-title"><span aria-hidden="true">{details.icon || '✦'}</span> {details.name}</h2>{details.description && <p className="goal-details-description">{details.description}</p>}<div className="goal-details-amount"><strong>{formatMoney(current)}</strong><span>{t.goalOf} {formatMoney(target)}</span><b>{progress}%</b></div><div className="progress-track" role="progressbar" aria-label={`${details.name} ${progress}%`} aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100"><span style={{ width: `${progress}%` }} /></div><p className="goal-next"><span>✦</span> {progress >= 100 ? t.goalAchieved : t.nextMilestone} <strong>{progress >= 100 ? '' : `${formatMoney(remaining)} ${t.remaining}`}</strong></p></div><div className="goal-details-art"><WarliArt image={warliGoal} alt={details.name} /></div></div><div className="goal-details-columns"><section className="goal-detail-panel" aria-labelledby="milestones-title"><p className="eyebrow">{t.milestones}</p><h3 id="milestones-title">{t.milestones}</h3><div className="milestone-list">{milestones.map((milestone, index) => { const amount = Number(milestone.amount); const isCompleted = milestone.is_completed || current >= amount; const isNext = !isCompleted && amount === Number(nextMilestone?.amount); return <div className={`milestone-item ${isCompleted ? 'is-completed' : ''} ${isNext ? 'is-next' : ''}`} key={milestone.id || `${amount}-${index}`}><span className="milestone-marker" aria-hidden="true">{isCompleted ? '✓' : isNext ? '◉' : '○'}</span><div><strong>{formatMoney(amount)}</strong><span>{t[['milestone25', 'milestone50', 'milestone75', 'milestone100'][index]] || milestone.title}</span>{isNext && <small>{formatMoney(Math.max(amount - current, 0))} {t.remaining}</small>}</div></div> })}</div></section><section className="goal-detail-panel" aria-labelledby="contributions-title"><p className="eyebrow">{t.contributions}</p><h3 id="contributions-title">{t.recentContributions}</h3>{details.contributions?.length ? <div className="contribution-list">{details.contributions.map((contribution) => <div className="contribution-row" key={contribution.id}><span>{formatContributionDate(contribution.contributed_at)}</span><strong>+{formatMoney(contribution.amount)}</strong></div>)}</div> : <p className="empty-copy">{t.noContributions}</p>}</section></div><button className="action-button terracotta-button goal-details-add" type="button" onClick={() => setShowContribution(true)} disabled={progress >= 100}>+ {t.addMoney}</button>{showContribution && <GoalModal t={t} title={`${t.addMoney} — ${details.name}`} onClose={() => setShowContribution(false)}><ContributionForm t={t} goal={details} onSaved={() => void reloadDetails()} onClose={() => setShowContribution(false)} /></GoalModal>}</section>
}

function LanguageSelect({ language, setLanguage, t }) {
  return <label className="auth-language"><span>{t.languageLabel}</span><select value={language} onChange={(event) => setLanguage(event.target.value)}>{languages.map((option) => <option value={option.code} key={option.code}>{option.label}</option>)}</select></label>
}

function LanguageGate({ language, setLanguage, onContinue }) {
  const [displayLanguage, setDisplayLanguage] = useState(language || 'en')
  const [locked, setLocked] = useState(Boolean(language))
  const displayTranslations = { ...translations[displayLanguage], ...extraTranslations[displayLanguage], ...authFlowTranslations[displayLanguage] }

  useEffect(() => {
    if (locked) return undefined
    const timer = window.setInterval(() => {
      setDisplayLanguage((current) => {
        const index = languages.findIndex((option) => option.code === current)
        return languages[(index + 1) % languages.length].code
      })
    }, 900)
    return () => window.clearInterval(timer)
  }, [locked])

  const chooseLanguage = (code) => {
    setLanguage(code)
    setDisplayLanguage(code)
    setLocked(true)
  }

  return <main className="auth-page"><section className="auth-card language-gate" aria-labelledby="language-gate-title"><div className="auth-card-top"><span className="brand-mark">{displayTranslations.brand}</span><span className="language-gate-step">1 / 2</span></div><p className="eyebrow">{displayTranslations.subtitle}</p><h1 id="language-gate-title" aria-live="polite">{displayTranslations.languageGateTitle}</h1><p className="auth-description" aria-live="polite">{displayTranslations.languageGateDescription}</p><div className="language-choice-list" role="radiogroup" aria-label={displayTranslations.languageLabel}>{languages.map((option) => <button className={language === option.code ? 'language-choice is-selected' : 'language-choice'} key={option.code} type="button" role="radio" aria-checked={language === option.code} onClick={() => chooseLanguage(option.code)}><span>{option.label}</span><span aria-hidden="true">{language === option.code ? '✓' : ''}</span></button>)}</div><button className="action-button terracotta-button" type="button" onClick={onContinue} disabled={!language}>{displayTranslations.languageContinue} <span aria-hidden="true">→</span></button></section></main>
}

function AuthPanel({ t, language, setLanguage }) {
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const normalizedEmail = email.trim()

  const submit = async (event) => {
    event.preventDefault()
    if (!supabase) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      if (mode === 'signup') {
        const { data, error: signUpError } = await supabase.auth.signUp({ email: normalizedEmail, password, options: { data: { display_name: name, preferred_language: language } } })
        if (signUpError) throw signUpError
        if (!data.session) {
          setMessage(t.authCheckEmail)
          setMode('signin')
          setPassword('')
        }
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email: normalizedEmail, password })
        if (signInError) throw signInError
      }
    } catch (authError) {
      setError(authError?.message || t.authError)
    } finally {
      setBusy(false)
    }
  }

  const googleSignIn = async () => {
    if (!supabase) return
    setBusy(true)
    setError('')
    const { error: oauthError } = await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin } })
    if (oauthError) { setError(oauthError.message || t.authError); setBusy(false) }
  }

  return <main className="auth-page"><section className="auth-card" aria-labelledby="auth-title"><div className="auth-card-top"><span className="brand-mark">{t.brand}</span><LanguageSelect language={language} setLanguage={setLanguage} t={t} /></div><p className="eyebrow">{t.subtitle}</p><h1 id="auth-title">{mode === 'signup' ? t.authSignupTitle : t.authTitle}</h1><p className="auth-description">{mode === 'signup' ? t.authSignupDescription : t.authDescription}</p>{!supabaseConfigured && <p className="manual-error" role="alert">{t.authError}</p>}<form className="auth-form" onSubmit={submit}>{mode === 'signup' && <label><span>{t.nameLabel}</span><input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required /></label>}<label><span>{t.emailLabel}</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label><label><span>{t.passwordLabel}</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} minLength="6" required /></label>{error && <p className="manual-error" role="alert">{error}</p>}{message && <p className="auth-message" role="status">{message}</p>}<button className="action-button terracotta-button" type="submit" disabled={busy || !supabaseConfigured}>{busy ? t.signingIn : mode === 'signup' ? t.signUp : t.signIn}</button></form><button className="google-button" type="button" onClick={googleSignIn} disabled={busy || !supabaseConfigured}>{t.googleSignIn}</button><button className="text-button auth-switch" type="button" onClick={() => { setMode(mode === 'signin' ? 'signup' : 'signin'); setError(''); setMessage('') }}>{mode === 'signin' ? t.authSwitchSignup : t.authSwitchSignin}</button></section></main>
}

function OnboardingPanel({ t, language, setLanguage, profile, onComplete }) {
  const [name, setName] = useState(profile.display_name || '')
  const [phone, setPhone] = useState(profile.phone_number || '')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    if (!consent) { setError(t.consentText); return }
    setBusy(true)
    setError('')
    try {
      const result = await updateProfile({ display_name: name.trim() || null, phone_number: phone.trim() || null, preferred_language: language, consent_accepted: true, onboarding_completed: true }, await getAccessToken())
      onComplete(result.profile)
    } catch (requestError) {
      setError(requestError?.message || t.authError)
    } finally {
      setBusy(false)
    }
  }

  return <main className="auth-page"><section className="auth-card" aria-labelledby="onboarding-title"><div className="auth-card-top"><span className="brand-mark">{t.brand}</span><LanguageSelect language={language} setLanguage={setLanguage} t={t} /></div><p className="eyebrow">{t.subtitle}</p><h1 id="onboarding-title">{t.onboardingTitle}</h1><p className="auth-description">{t.onboardingDescription}</p><form className="auth-form" onSubmit={submit}><label><span>{t.nameLabel}</span><input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" /></label><label><span>{t.profilePhone}</span><input type="tel" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91…" autoComplete="tel" /></label><label className="consent-field"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} required /><span>{t.consentText}</span></label>{error && <p className="manual-error" role="alert">{error}</p>}<button className="action-button terracotta-button" type="submit" disabled={busy}>{busy ? t.signingIn : t.finishOnboarding}</button></form></section></main>
}

function ConversationPanel({ t, language, onSaved }) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const send = async (event) => {
    event.preventDefault()
    const trimmed = message.trim()
    if (!trimmed || busy) return
    setBusy(true)
    setError('')
    setMessages((current) => [...current, { role: 'user', text: trimmed }])
    setMessage('')
    try {
      const result = await sendConversationMessage({ message: trimmed, conversation_id: conversationId, channel: 'web', language }, await getAccessToken())
      setConversationId(result.conversation_id)
      setMessages((current) => [...current, { role: 'assistant', text: result.response, proposal: result.transaction_proposal }])
    } catch (requestError) {
      setError(requestError?.message || t.responseError)
    } finally {
      setBusy(false)
    }
  }

  const confirm = async (proposalId) => {
    try {
      await confirmTransactionProposal(proposalId, await getAccessToken())
      onSaved?.()
      setMessages((current) => current.map((item) => item.proposal?.id === proposalId ? { ...item, proposal: null, text: `${item.text}\n\n${t.confirmSaved}` } : item))
    } catch (requestError) {
      setError(requestError?.message || t.responseError)
    }
  }

  return <section className="section-shell conversation-section" id="conversation-panel" aria-labelledby="conversation-title"><div className="section-heading"><p className="eyebrow">{t.talk}</p><h2 id="conversation-title">{t.chatTitle}</h2></div><div className="conversation-log" aria-live="polite">{messages.length === 0 && <p className="empty-copy">{t.noData}</p>}{messages.map((item, index) => <div className={`conversation-message ${item.role}`} key={`${item.role}-${index}`}><span>{item.text}</span>{item.proposal && <button className="text-button" type="button" onClick={() => confirm(item.proposal.id)}>{t.confirmAction}</button>}</div>)}</div>{error && <p className="manual-error" role="alert">{error}</p>}<form className="conversation-form" onSubmit={send}><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder={t.chatPlaceholder} aria-label={t.chatPlaceholder} maxLength="4000" /><button className="action-button terracotta-button" type="submit" disabled={busy}>{busy ? '…' : t.send}</button></form></section>
}

function VoiceLogging({ t, language, onSaved }) {
  const [voiceState, setVoiceState] = useState('default')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [draft, setDraft] = useState(null)
  const [error, setError] = useState('')
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const callIdRef = useRef(null)

  useEffect(() => () => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
    streamRef.current?.getTracks().forEach((track) => track.stop())
  }, [])

  const makeId = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`

  const audioToBase64 = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(String(reader.result || '').split(',')[1] || '')
    reader.onerror = () => reject(new Error(t.voiceSendError))
    reader.readAsDataURL(blob)
  })

  const missingPrompt = (missingField) => ({
    transaction_type: t.voiceAskType,
    amount: t.voiceAskAmount,
    purpose: t.voiceAskPurpose,
  })[missingField] || t.voiceRecordResponse

  const saveConfirmedTransaction = async (transaction, rawStatement) => {
    if (!transaction?.transaction_type || !transaction.amount || !transaction.purpose) return
    setVoiceState('saving')
    setError('')
    try {
      const proposal = await createTransactionProposal({
        transaction_type: transaction.transaction_type,
        amount: Number(transaction.amount),
        currency: 'INR',
        category: null,
        description: transaction.purpose,
        date: localTransactionDate(),
        source: 'browser_voice',
        confidence: 0.9,
        raw_statement: rawStatement || transaction.purpose,
        goal_id: null,
      }, await getAccessToken())
      await confirmTransactionProposal(proposal.id, await getAccessToken())
      setResponse(t.voiceConfirmed)
      setVoiceState('success')
      onSaved?.()
    } catch (requestError) {
      setError(requestError?.message || t.voiceSendError)
      setVoiceState('result')
    }
  }

  const submitRecordedAudio = async (recorder) => {
    try {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
      if (!blob.size) throw new Error(t.voiceNoTransaction)
      const result = await transcribeBrowserVoice({
        call_id: callIdRef.current,
        audio_base64: await audioToBase64(blob),
        audio_mime_type: blob.type || 'audio/webm',
        idempotency_key: makeId(),
      }, await getAccessToken())
      const heard = result.transcript?.trim() || ''
      if (!heard) throw new Error(t.voiceNoTransaction)
      setTranscript(heard)
      if (draft && isConfirmation(heard) && draft.missing?.length === 0) {
        await saveConfirmedTransaction(draft, `${transcript} ${heard}`.trim())
        return
      }
      const nextDraft = mergeVoiceTransaction(draft, heard)
      setDraft(nextDraft)
      if (draft && isRejection(heard)) {
        setResponse(nextDraft.missing.length ? missingPrompt(nextDraft.missing[0]) : describeVoiceTransaction(nextDraft, language))
        setVoiceState('result')
        return
      }
      if (nextDraft.missing.length) {
        setResponse(missingPrompt(nextDraft.missing[0]))
        setVoiceState('result')
        return
      }
      setResponse(describeVoiceTransaction(nextDraft, language))
      setVoiceState('confirming')
    } catch (requestError) {
      setError(requestError?.message || t.voiceSendError)
      setVoiceState('result')
    } finally {
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      recorderRef.current = null
    }
  }

  const startRecording = async () => {
    setError('')
    if (!globalThis.navigator?.mediaDevices?.getUserMedia || !globalThis.MediaRecorder) {
      setError(t.voiceUnsupported)
      return
    }
    if (!callIdRef.current || voiceState === 'success') {
      callIdRef.current = `browser-${makeId()}`
      setTranscript('')
      setResponse('')
      setDraft(null)
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []
      const preferredTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus']
      const supportedType = preferredTypes.find((type) => MediaRecorder.isTypeSupported?.(type))
      const recorder = supportedType ? new MediaRecorder(stream, { mimeType: supportedType }) : new MediaRecorder(stream)
      recorder.ondataavailable = (event) => {
        if (event.data?.size) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => { void submitRecordedAudio(recorder) }
      recorderRef.current = recorder
      recorder.start()
      setVoiceState('listening')
    } catch (requestError) {
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      setError(requestError?.name === 'NotAllowedError' ? t.voicePermission : t.voiceSendError)
      setVoiceState('default')
    }
  }

  const stopRecording = () => {
    if (recorderRef.current?.state === 'recording') {
      setVoiceState('processing')
      recorderRef.current.stop()
    }
  }

  const reset = () => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
    streamRef.current?.getTracks().forEach((track) => track.stop())
    recorderRef.current = null
    streamRef.current = null
    chunksRef.current = []
    callIdRef.current = null
    setVoiceState('default')
    setTranscript('')
    setResponse('')
    setDraft(null)
    setError('')
  }

  const content = {
    default: { eyebrow: t.voiceEyebrow, title: t.voiceTitle, copy: t.voiceCopy, button: t.recordStart },
    listening: { eyebrow: t.listening, title: t.listeningTitle, copy: t.listeningCopy, button: t.recordStop },
    processing: { eyebrow: t.words, title: t.voiceProcessing, copy: t.voiceCopy, button: t.voiceProcessing },
    result: { eyebrow: t.voiceResponse, title: transcript || t.words, copy: response || t.voiceNoTransaction, button: t.voiceRecordResponse },
    confirming: { eyebrow: t.proposalPending, title: transcript || t.words, copy: response || t.confirmVoice, button: t.confirmAction },
    saving: { eyebrow: t.proposalPending, title: t.voiceProcessing, copy: t.voiceProcessing, button: t.voiceProcessing },
    success: { eyebrow: t.finished, title: t.confirmSaved, copy: response || t.voiceConfirmed, button: t.another },
  }[voiceState]

  return <article id="voice-logging" className={`action-card voice-card voice-${voiceState}`}>
    <div className="action-icon" aria-hidden="true"><span className="sound-wave">)))</span></div>
    <p className="eyebrow">{content.eyebrow}</p>
    <h3>{content.title}</h3>
    <p className="action-copy">{content.copy}</p>
    {error && <p className="manual-error" role="alert">{error}</p>}
    {draft && voiceState === 'confirming' && <p className="manual-summary"><strong>{draft.transaction_type === 'income' ? t.incomeOption : t.expenditureOption}</strong><span>₹{draft.amount}</span><span>{draft.purpose}</span></p>}
    {voiceState === 'listening' ? <button className="action-button terracotta-button" type="button" onClick={stopRecording}>{content.button} <span aria-hidden="true">■</span></button> : voiceState === 'processing' || voiceState === 'saving' ? <button className="action-button green-button" type="button" disabled>{content.button}</button> : voiceState === 'confirming' && draft ? <><button className="action-button green-button" type="button" onClick={() => void saveConfirmedTransaction(draft, transcript)}>{t.confirmAction} <span aria-hidden="true">→</span></button><button className="text-button" type="button" onClick={() => void startRecording()}>{t.voiceRecordResponse}</button><button className="text-button" type="button" onClick={reset}>{t.editAction}</button></> : <button className="action-button green-button" type="button" onClick={() => void startRecording()}>{content.button} <span aria-hidden="true">{voiceState === 'success' ? '↻' : '→'}</span></button>}
  </article>
}

const extraTranslations = {
  te: {
    authTitle: 'శ్రీలోకి స్వాగతం', authSignupTitle: 'మీ ఖాతాను సృష్టించండి', authDescription: 'మీ ఆర్థిక ప్రయాణాన్ని కొనసాగించడానికి సైన్ ఇన్ చేయండి.', authSignupDescription: 'మీ ఆర్థిక ప్రయాణాన్ని ప్రారంభించడానికి మీ వివరాలను నమోదు చేయండి.', emailLabel: 'ఈమెయిల్', passwordLabel: 'పాస్‌వర్డ్', nameLabel: 'పేరు', signIn: 'సైన్ ఇన్', signUp: 'ఖాతా తెరవండి', googleSignIn: 'Googleతో కొనసాగండి', signingIn: 'దయచేసి వేచి ఉండండి…', authSwitchSignup: 'కొత్తవారా? ఖాతా తెరవండి', authSwitchSignin: 'ఇప్పటికే ఖాతా ఉందా? సైన్ ఇన్ చేయండి', authError: 'సైన్ ఇన్ కాలేదు. వివరాలను తనిఖీ చేసి మళ్లీ ప్రయత్నించండి.', authCheckEmail: 'మీ ఈమెయిల్‌ను ధృవీకరించడానికి పంపిన లింక్‌ను తెరిచి, అదే ఈమెయిల్ మరియు పాస్‌వర్డ్‌తో సైన్ ఇన్ చేయండి.', signOut: 'సైన్ అవుట్', loading: 'లోడ్ అవుతోంది…', loadError: 'మీ సమాచారాన్ని లోడ్ చేయలేకపోయాం.', voiceUnsupported: 'ఈ బ్రౌజర్‌లో మైక్రోఫోన్ వాయిస్ అందుబాటులో లేదు.', voicePermission: 'మైక్రోఫోన్ అనుమతి అవసరం.', voiceSendError: 'వాయిస్‌ను పంపలేకపోయాం. మళ్లీ ప్రయత్నించండి.', voiceResponse: 'సహచరి చెప్పింది', chatTitle: 'మీ సహచరితో మాట్లాడండి', chatPlaceholder: 'మీ ప్రశ్నను ఇక్కడ రాయండి…', send: 'పంపండి', talk: 'మాట్లాడండి', recordStart: 'వాయిస్ రికార్డ్ చేయండి', recordStop: 'రికార్డింగ్ ఆపండి', voiceProcessing: 'మీ మాటను అర్థం చేసుకుంటున్నాను…', confirmVoice: 'ఈ ఎంట్రీని నమోదు చేయనా?', confirmSaved: 'నమోదు అయింది', proposalPending: 'నిర్ధారణ అవసరం', confirmAction: 'నిర్ధారించండి', editAction: 'మార్చండి', profilePhone: 'ఫోన్ నంబర్', phoneRequired: 'ఫీచర్ ఫోన్ వాయిస్ కోసం మీ ఫోన్ నంబర్‌ను ప్రొఫైల్‌లో జోడించండి.', noData: 'ఇంకా సమాచారం లేదు.', signInToUse: 'ఈ ఫీచర్ ఉపయోగించడానికి సైన్ ఇన్ చేయండి.', dashboardError: 'డాష్‌బోర్డ్‌ను లోడ్ చేయలేకపోయాం.', refresh: 'మళ్లీ ప్రయత్నించండి', responseError: 'సందేశానికి సమాధానం రాలేదు.', storyAction: 'కథ గురించి మాట్లాడుదాం', storyPrompt: 'నాకు ఒక నిజ జీవిత ఆర్థిక కథ చెప్పండి.', voiceCallInfo: 'ఫీచర్ ఫోన్ కాల్ ప్రారంభించడానికి మీ నమోదైన నంబర్‌కు కాల్ చేయండి.', browserVoice: 'బ్రౌజర్ వాయిస్', transactionHistory: 'ఇటీవలి లావాదేవీలు', noTransactions: 'ఇంకా లావాదేవీలు లేవు.', incomeRecorded: 'ఆదాయం', expenseRecorded: 'ఖర్చు', date: 'తేదీ', status: 'స్థితి', pending: 'నిర్ధారణ కోసం వేచి ఉంది', confirmed: 'నిర్ధారించబడింది', account: 'ఖాతా', onboardingTitle: 'ముందుగా మిమ్మల్ని తెలుసుకుందాం', onboardingDescription: 'మీ భాష, పేరు మరియు ఫోన్ నంబర్‌ను జోడించండి. ఫోన్ నంబర్ వాయిస్ గుర్తింపుకు ఉపయోగపడుతుంది.', consentText: 'నా సమాచారాన్ని నా ఆర్థిక సహచరి కోసం ఉపయోగించడానికి నేను అంగీకరిస్తున్నాను.', finishOnboarding: 'ప్రారంభిద్దాం', goalNameField: 'లక్ష్యం పేరు', goalTargetField: 'లక్ష్య మొత్తం', createGoal: 'లక్ష్యాన్ని సృష్టించండి',
  },
  hi: {
    authTitle: 'श्री में आपका स्वागत है', authSignupTitle: 'अपना खाता बनाएं', authDescription: 'अपनी आर्थिक यात्रा जारी रखने के लिए साइन इन करें।', authSignupDescription: 'अपनी आर्थिक यात्रा शुरू करने के लिए विवरण भरें।', emailLabel: 'ईमेल', passwordLabel: 'पासवर्ड', nameLabel: 'नाम', signIn: 'साइन इन', signUp: 'खाता बनाएं', googleSignIn: 'Google से जारी रखें', signingIn: 'कृपया प्रतीक्षा करें…', authSwitchSignup: 'नए हैं? खाता बनाएं', authSwitchSignin: 'पहले से खाता है? साइन इन करें', authError: 'साइन इन नहीं हो सका। विवरण जाँचकर फिर कोशिश करें।', authCheckEmail: 'ईमेल सत्यापित करने वाले लिंक को खोलें, फिर उसी ईमेल और पासवर्ड से साइन इन करें।', signOut: 'साइन आउट', loading: 'लोड हो रहा है…', loadError: 'आपकी जानकारी लोड नहीं हो सकी।', voiceUnsupported: 'इस ब्राउज़र में माइक्रोफ़ोन वॉइस उपलब्ध नहीं है।', voicePermission: 'माइक्रोफ़ोन की अनुमति ज़रूरी है।', voiceSendError: 'वॉइस भेजी नहीं जा सकी। फिर कोशिश करें।', voiceResponse: 'साथी ने कहा', chatTitle: 'अपने साथी से बात करें', chatPlaceholder: 'अपना सवाल यहाँ लिखें…', send: 'भेजें', talk: 'बात करें', recordStart: 'वॉइस रिकॉर्ड करें', recordStop: 'रिकॉर्डिंग रोकें', voiceProcessing: 'आपकी बात समझ रही हूँ…', confirmVoice: 'क्या यह एंट्री दर्ज करें?', confirmSaved: 'दर्ज हो गया', proposalPending: 'पुष्टि ज़रूरी है', confirmAction: 'पुष्टि करें', editAction: 'बदलें', profilePhone: 'फ़ोन नंबर', phoneRequired: 'फ़ीचर फोन वॉइस के लिए अपना फ़ोन नंबर प्रोफ़ाइल में जोड़ें।', noData: 'अभी कोई जानकारी नहीं है।', signInToUse: 'इस सुविधा के लिए साइन इन करें।', dashboardError: 'डैशबोर्ड लोड नहीं हो सका।', refresh: 'फिर कोशिश करें', responseError: 'संदेश का जवाब नहीं मिला।', storyAction: 'कहानी पर बात करें', storyPrompt: 'मुझे एक सच्ची आर्थिक कहानी सुनाइए।', voiceCallInfo: 'फ़ीचर फोन से बात करने के लिए अपने पंजीकृत नंबर पर कॉल करें।', browserVoice: 'ब्राउज़र वॉइस', transactionHistory: 'हाल की लेन-देन', noTransactions: 'अभी कोई लेन-देन नहीं है।', incomeRecorded: 'आमदनी', expenseRecorded: 'खर्च', date: 'तारीख', status: 'स्थिति', pending: 'पुष्टि बाकी', confirmed: 'पुष्टि हो गई', account: 'खाता', onboardingTitle: 'पहले आपको जानें', onboardingDescription: 'अपनी भाषा, नाम और फ़ोन नंबर जोड़ें। फ़ोन नंबर वॉइस पहचान के लिए उपयोग होगा।', consentText: 'मैं अपनी जानकारी को अपने आर्थिक साथी के लिए उपयोग करने की सहमति देता/देती हूँ।', finishOnboarding: 'शुरू करें', goalNameField: 'लक्ष्य का नाम', goalTargetField: 'लक्ष्य राशि', createGoal: 'लक्ष्य बनाएं',
  },
  en: {
    authTitle: 'Welcome to Shree', authSignupTitle: 'Create your account', authDescription: 'Sign in to continue your financial journey.', authSignupDescription: 'Add your details to begin your financial journey.', emailLabel: 'Email', passwordLabel: 'Password', nameLabel: 'Name', signIn: 'Sign in', signUp: 'Create account', googleSignIn: 'Continue with Google', signingIn: 'Please wait…', authSwitchSignup: 'New here? Create an account', authSwitchSignin: 'Already have an account? Sign in', authError: 'Could not sign in. Check your details and try again.', authCheckEmail: 'Open the email verification link, then sign in with the same email and password.', signOut: 'Sign out', loading: 'Loading…', loadError: 'We could not load your information.', voiceUnsupported: 'Microphone voice is not available in this browser.', voicePermission: 'Microphone permission is required.', voiceSendError: 'We could not send the voice message. Please try again.', voiceResponse: 'Your companion said', chatTitle: 'Talk with your companion', chatPlaceholder: 'Write your question here…', send: 'Send', talk: 'Talk', recordStart: 'Record voice', recordStop: 'Stop recording', voiceProcessing: 'Understanding your words…', confirmVoice: 'Record this entry?', confirmSaved: 'Recorded', proposalPending: 'Confirmation needed', confirmAction: 'Confirm', editAction: 'Change', profilePhone: 'Phone number', phoneRequired: 'Add your phone number to your profile for feature-phone voice.', noData: 'No information yet.', signInToUse: 'Sign in to use this feature.', dashboardError: 'We could not load the dashboard.', refresh: 'Try again', responseError: 'We did not receive a response.', storyAction: 'Talk about this story', storyPrompt: 'Tell me a realistic financial story.', voiceCallInfo: 'To use feature-phone voice, call from your registered phone number.', browserVoice: 'Browser voice', transactionHistory: 'Recent transactions', noTransactions: 'No transactions yet.', incomeRecorded: 'Income', expenseRecorded: 'Expense', date: 'Date', status: 'Status', pending: 'Pending confirmation', confirmed: 'Confirmed', account: 'Account', onboardingTitle: 'Let us get to know you', onboardingDescription: 'Add your language, name, and phone number. Your phone number enables feature-phone voice.', consentText: 'I agree that my information can be used by my financial companion.', finishOnboarding: 'Get started', goalNameField: 'Goal name', goalTargetField: 'Goal amount', createGoal: 'Create goal',
  },
}

const authFlowTranslations = {
  te: {
    languageGateTitle: 'మీ భాషను ఎంచుకోండి', languageGateDescription: 'ముందుగా మీకు ఇష్టమైన భాషను ఎంచుకోండి. శ్రీలోని ప్రతి సందేశం అదే భాషలో ఉంటుంది.', languageContinue: 'కొనసాగండి', phoneLabel: 'ఫోన్ నంబర్', verificationCodeLabel: 'ధృవీకరణ కోడ్', verifyPhone: 'ఫోన్ ధృవీకరించండి', resendCode: 'కోడ్ మళ్లీ పంపండి', authCheckPhone: 'మీ ఫోన్‌కు వచ్చిన SMSలోని కోడ్‌ను నమోదు చేయండి.', authPhoneSetup: 'ఖాతా సృష్టించబడింది. ఇప్పుడు అదే ఫోన్ నంబర్ మరియు పాస్‌వర్డ్‌తో సైన్ ఇన్ చేయండి.',
  },
  hi: {
    languageGateTitle: 'अपनी भाषा चुनें', languageGateDescription: 'पहले अपनी पसंदीदा भाषा चुनें। श्री के सभी संदेश उसी भाषा में होंगे।', languageContinue: 'जारी रखें', phoneLabel: 'फ़ोन नंबर', verificationCodeLabel: 'सत्यापन कोड', verifyPhone: 'फ़ोन सत्यापित करें', resendCode: 'कोड फिर भेजें', authCheckPhone: 'आपके फ़ोन पर आए SMS का कोड दर्ज करें।', authPhoneSetup: 'खाता बन गया है। अब उसी फ़ोन नंबर और पासवर्ड से साइन इन करें।',
  },
  en: {
    languageGateTitle: 'Choose your language', languageGateDescription: 'Choose your preferred language first. Everything in Shree will use this language.', languageContinue: 'Continue', phoneLabel: 'Phone number', verificationCodeLabel: 'Verification code', verifyPhone: 'Verify phone', resendCode: 'Resend code', authCheckPhone: 'Enter the code sent to your phone by SMS.', authPhoneSetup: 'Your account was created. Sign in now with the same phone number and password.',
  },
}

const firstUserTranslations = {
  te: {
    newUserEyebrow: 'మీ ప్రయాణం ఇక్కడ మొదలవుతుంది', newUserTitle: 'మీ కథతో మొదలుపెడదాం', newUserCopy: 'మీ ఆర్థిక చిత్రం సిద్ధంగా ఉంది. మొదటి ఆదాయం లేదా ఖర్చును నమోదు చేయడానికి కాల్ చేయండి లేదా మీ మాటలను రికార్డ్ చేయండి.', newUserCall: 'కాల్ చేయండి', newUserRecord: 'రికార్డింగ్ ప్రారంభించండి',
  },
  hi: {
    newUserEyebrow: 'आपकी यात्रा यहीं से शुरू होती है', newUserTitle: 'आपकी कहानी से शुरुआत करें', newUserCopy: 'आपकी आर्थिक तस्वीर तैयार है। अपनी पहली आमदनी या खर्च दर्ज करने के लिए कॉल करें या अपनी बात रिकॉर्ड करें।', newUserCall: 'कॉल करें', newUserRecord: 'रिकॉर्डिंग शुरू करें',
  },
  en: {
    newUserEyebrow: 'Your journey starts here', newUserTitle: 'Let’s begin with your story', newUserCopy: 'Your financial picture is ready. Take a call or record your first income or expense so your companion can get to know you.', newUserCall: 'Take a call', newUserRecord: 'Start recording',
  },
}

const goalTranslations = {
  te: {
    goalsTitle: 'నా లక్ష్యాలు', addGoal: 'లక్ష్యాన్ని జోడించండి', saveMoney: 'డబ్బు దాచండి', activeGoals: 'ప్రస్తుత లక్ష్యాలు', completedGoals: 'పూర్తైన లక్ష్యాలు', noGoals: 'మీకు ఇంకా పొదుపు లక్ష్యం లేదు.', createFirstGoal: 'ముఖ్యమైన దానితో ప్రారంభించండి.', addMoney: 'డబ్బు జోడించండి', currentSaved: 'ఇప్పటి వరకు దాచింది', goalOf: 'లో', nextMilestone: 'తదుపరి మైలురాయి', remaining: 'ఇంకా', goalAchieved: 'లక్ష్యం పూర్తైంది!', categoryLabel: 'వర్గం', targetDateLabel: 'లక్ష్య తేదీ', optional: 'ఐచ్ఛికం', iconLabel: 'చిహ్నం', descriptionLabel: 'వివరణ', descriptionPlaceholder: 'ఈ లక్ష్యం గురించి చిన్న గమనిక', cancel: 'రద్దు చేయండి', saveAmount: 'ఎంత దాచాలనుకుంటున్నారు?', afterSaving: 'దాచిన తర్వాత', allocatePrompt: 'ఈ మొత్తాన్ని ఏ లక్ష్యాలకు కేటాయించాలి?', todaySavings: 'ఈరోజు పొదుపు', allocationTotal: 'మొత్తం', allocationMismatch: 'కేటాయించిన మొత్తం పొదుపు మొత్తానికి సమానంగా ఉండాలి.', contributionError: 'డబ్బును జోడించలేకపోయాం. మళ్లీ ప్రయత్నించండి.', contributionAdded: 'మీ పొదుపు జోడించబడింది.', back: 'వెనక్కి', milestones: 'మైలురాళ్లు', contributions: 'చందాలు', recentContributions: 'ఇటీవలి పొదుపులు', noContributions: 'ఇంకా చందాలు లేవు.', goalLoadError: 'లక్ష్య వివరాలను లోడ్ చేయలేకపోయాం.', business: 'వ్యాపారం', education: 'విద్య', home: 'ఇల్లు', farming: 'వ్యవసాయం', livestock: 'పశుసంపద', marriage: 'వివాహం', emergency: 'అత్యవసరం', general: 'సాధారణ పొదుపు', other: 'ఇతర', milestone25: 'మొదటి మైలురాయి', milestone50: 'మధ్యంతర మైలురాయి', milestone75: 'ముఖ్యమైన మైలురాయి', milestone100: 'లక్ష్యం పూర్తైంది', createGoal: 'లక్ష్యాన్ని సృష్టించండి', goalNameField: 'లక్ష్యం పేరు', goalTargetField: 'లక్ష్య మొత్తం', goalTargetHint: 'మీకు ఎంత అవసరం?',
  },
  hi: {
    goalsTitle: 'मेरे लक्ष्य', addGoal: 'लक्ष्य जोड़ें', saveMoney: 'पैसे बचाएं', activeGoals: 'चल रहे लक्ष्य', completedGoals: 'पूरे हुए लक्ष्य', noGoals: 'अभी आपका कोई बचत लक्ष्य नहीं है।', createFirstGoal: 'किसी ज़रूरी चीज़ से शुरुआत करें।', addMoney: 'पैसे जोड़ें', currentSaved: 'अब तक बचत', goalOf: 'में से', nextMilestone: 'अगला पड़ाव', remaining: 'बाकी', goalAchieved: 'लक्ष्य पूरा हुआ!', categoryLabel: 'श्रेणी', targetDateLabel: 'लक्ष्य की तारीख', optional: 'वैकल्पिक', iconLabel: 'चिह्न', descriptionLabel: 'विवरण', descriptionPlaceholder: 'इस लक्ष्य के बारे में छोटी जानकारी', cancel: 'रद्द करें', saveAmount: 'आप कितना बचाना चाहते हैं?', afterSaving: 'बचत के बाद', allocatePrompt: 'यह राशि किन लक्ष्यों में बांटनी है?', todaySavings: 'आज की बचत', allocationTotal: 'कुल', allocationMismatch: 'बांटी गई राशि बचत की कुल राशि के बराबर होनी चाहिए।', contributionError: 'पैसे जोड़ नहीं सके। फिर कोशिश करें।', contributionAdded: 'आपकी बचत जोड़ दी गई।', back: 'वापस', milestones: 'पड़ाव', contributions: 'योगदान', recentContributions: 'हाल की बचत', noContributions: 'अभी कोई योगदान नहीं है।', goalLoadError: 'लक्ष्य का विवरण लोड नहीं हो सका।', business: 'व्यवसाय', education: 'शिक्षा', home: 'घर', farming: 'खेती', livestock: 'पशुधन', marriage: 'शादी', emergency: 'आपातकाल', general: 'सामान्य बचत', other: 'अन्य', milestone25: 'पहला पड़ाव', milestone50: 'मध्य पड़ाव', milestone75: 'महत्वपूर्ण पड़ाव', milestone100: 'लक्ष्य पूरा', createGoal: 'लक्ष्य बनाएं', goalNameField: 'लक्ष्य का नाम', goalTargetField: 'लक्ष्य राशि', goalTargetHint: 'आपको कितनी राशि चाहिए?',
  },
  en: {
    goalsTitle: 'My Goals', addGoal: 'Add Goal', saveMoney: 'Save money', activeGoals: 'Active goals', completedGoals: 'Completed goals', noGoals: "You don't have a savings goal yet.", createFirstGoal: 'Start with something important to you.', addMoney: 'Add money', currentSaved: 'Saved so far', goalOf: 'of', nextMilestone: 'Next milestone', remaining: 'remaining', goalAchieved: 'Goal achieved!', categoryLabel: 'Category', targetDateLabel: 'Target date', optional: 'Optional', iconLabel: 'Icon', descriptionLabel: 'Description', descriptionPlaceholder: 'A short note about this goal', cancel: 'Cancel', saveAmount: 'How much would you like to save?', afterSaving: 'After saving', allocatePrompt: 'Where would you like to save it?', todaySavings: "Today's savings", allocationTotal: 'Total', allocationMismatch: 'The allocation total must equal the savings amount.', contributionError: 'We could not add the money. Please try again.', contributionAdded: 'Your saving was added.', back: 'Back', milestones: 'Milestones', contributions: 'Contributions', recentContributions: 'Recent contributions', noContributions: 'No contributions yet.', goalLoadError: 'We could not load the goal details.', business: 'Business', education: 'Education', home: 'Home', farming: 'Farming', livestock: 'Livestock', marriage: 'Marriage', emergency: 'Emergency', general: 'General savings', other: 'Other', milestone25: 'First milestone', milestone50: 'Progress milestone', milestone75: 'Major milestone', milestone100: 'Goal completed', createGoal: 'Create goal', goalNameField: 'Goal name', goalTargetField: 'Target amount', goalTargetHint: 'How much do you need?',
  },
}

const storyTranslations = {
  te: {
    storyLoading: 'కథను సిద్ధం చేస్తున్నాం…', storyPause: 'ఆపండి', storyContinue: 'కొనసాగించండి', storyAgain: 'మళ్లీ వినండి', storyProgress: 'కథలో భాగం', storyError: 'కథను వినిపించలేకపోయాం. మళ్లీ ప్రయత్నించండి.', storyTextLabel: 'కథలోని మాటలు',
  },
  hi: {
    storyLoading: 'कहानी तैयार हो रही है…', storyPause: 'रोकें', storyContinue: 'जारी रखें', storyAgain: 'फिर सुनें', storyProgress: 'कहानी का भाग', storyError: 'कहानी सुनाई नहीं जा सकी। फिर कोशिश करें।', storyTextLabel: 'कहानी के शब्द',
  },
  en: {
    storyLoading: 'Preparing the story…', storyPause: 'Pause', storyContinue: 'Continue', storyAgain: 'Hear it again', storyProgress: 'Story part', storyError: 'We could not play the story. Please try again.', storyTextLabel: 'Story words',
  },
}

const voiceFlowTranslations = {
  te: {
    voiceResponse: 'లావాదేవీ వివరాలు', voiceAskType: 'ఇది ఆదాయమా లేదా ఖర్చా?', voiceAskAmount: 'ఎంత మొత్తం?', voiceAskPurpose: 'ఆ డబ్బును దేనికి ఖర్చు చేశారు లేదా ఎక్కడి నుంచి వచ్చింది?', voiceRecordResponse: 'మీ సమాధానాన్ని రికార్డ్ చేయండి', voiceFocus: 'ఆదాయం లేదా ఖర్చును నమోదు చేయడానికి మాత్రమే మాట్లాడండి.', voiceConfirmed: 'ధృవీకరించబడింది. ఈ ఎంట్రీ Supabaseలో సేవ్ అయింది.', voiceNoTransaction: 'లావాదేవీ వివరాలు వినిపించలేదు. మళ్లీ చెప్పండి.', voiceRecognitionError: 'వాయిస్ వినలేకపోయాం. మైక్రోఫోన్ అనుమతిని తనిఖీ చేసి మళ్లీ ప్రయత్నించండి.',
  },
  hi: {
    voiceResponse: 'लेन-देन का विवरण', voiceAskType: 'यह आमदनी है या खर्च?', voiceAskAmount: 'राशि कितनी थी?', voiceAskPurpose: 'यह पैसा किस पर खर्च हुआ या कहाँ से मिला?', voiceRecordResponse: 'अपना जवाब रिकॉर्ड करें', voiceFocus: 'कृपया केवल आमदनी या खर्च दर्ज करने के लिए बोलें।', voiceConfirmed: 'पुष्टि हो गई। यह एंट्री Supabase में सेव हो गई।', voiceNoTransaction: 'लेन-देन की जानकारी सुनाई नहीं दी। फिर बोलें।', voiceRecognitionError: 'वॉइस समझ नहीं आई। माइक्रोफ़ोन की अनुमति जाँचकर फिर कोशिश करें।',
  },
  en: {
    voiceResponse: 'Transaction details', voiceAskType: 'Was that income or an expense?', voiceAskAmount: 'How much was the amount?', voiceAskPurpose: 'What was the money spent on, or where did it come from?', voiceRecordResponse: 'Record your response', voiceFocus: 'Please speak only about an income or expense to record it.', voiceConfirmed: 'Confirmed. This entry has been saved to Supabase.', voiceNoTransaction: 'I did not hear a transaction. Please try again.', voiceRecognitionError: 'I could not hear your voice. Check microphone permission and try again.',
  },
}

function NewUserStart({ t }) {
  return <section className="section-shell new-user-start" aria-labelledby="new-user-start-title"><p className="eyebrow">{t.newUserEyebrow}</p><h2 id="new-user-start-title">{t.newUserTitle}</h2><p>{t.newUserCopy}</p></section>
}

function ManualEntry({ t, onSaved }) {
  const [transactionType, setTransactionType] = useState('income')
  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('')
  const [proposal, setProposal] = useState(null)
  const [state, setState] = useState('idle')
  const [error, setError] = useState('')

  const reset = () => {
    setProposal(null)
    setState('idle')
    setError('')
  }

  const submitProposal = async (event) => {
    event.preventDefault()
    const numericAmount = Number(amount)
    if (!Number.isFinite(numericAmount) || numericAmount <= 0 || !reason.trim()) {
      setError(t.entryError)
      return
    }

    setError('')
    setState('submitting')
    try {
      const accessToken = await getAccessToken()
      const nextProposal = await createTransactionProposal({
        transaction_type: transactionType,
        amount: numericAmount,
        currency: 'INR',
        category: null,
        description: reason.trim(),
        date: localTransactionDate(),
        source: 'web',
        confidence: 1,
        raw_statement: `${transactionType}: ${reason.trim()}`,
        goal_id: null,
      }, accessToken)
      setProposal(nextProposal)
      setState('pending')
    } catch (requestError) {
      setError(requestError?.message || t.entryError)
      setState('idle')
    }
  }

  const confirmProposal = async () => {
    if (!proposal?.id) return
    setError('')
    setState('confirming')
    try {
      const accessToken = await getAccessToken()
      await confirmTransactionProposal(proposal.id, accessToken)
      onSaved?.()
      setState('success')
    } catch (requestError) {
      setError(requestError?.message || t.confirmError)
      setState('pending')
    }
  }

  const isBusy = state === 'submitting' || state === 'confirming'
  const typeLabel = transactionType === 'income' ? t.incomeOption : t.expenditureOption

  return <article className="action-card manual-card">
    <div className="action-icon manual-icon" aria-hidden="true">✎</div>
    {state === 'pending' || state === 'confirming' ? <div className="manual-result">
      <p className="eyebrow">{t.pendingEyebrow}</p>
      <h3>{t.pendingTitle}</h3>
      <p className="manual-summary"><strong>{typeLabel}</strong><span>₹{proposal.amount}</span><span>{proposal.description}</span></p>
      <p className="action-copy">{t.pendingCopy}</p>
      {error && <p className="manual-error" role="alert">{error}</p>}
      <button className="action-button terracotta-button" type="button" onClick={confirmProposal} disabled={isBusy}>{isBusy ? '…' : t.confirmEntry} <span aria-hidden="true">→</span></button>
      <button className="text-button" type="button" onClick={reset} disabled={isBusy}>{t.editEntry}</button>
    </div> : state === 'success' ? <div className="manual-result" role="status">
      <p className="eyebrow">{t.finished}</p>
      <h3 className="manual-success">{transactionType === 'income' ? t.savedIncome : t.savedExpense}</h3>
      <p className="action-copy">{t.entryFresh}</p>
      <button className="action-button green-button" type="button" onClick={reset}>{t.another} <span aria-hidden="true">↻</span></button>
    </div> : <>
      <p className="eyebrow">{t.manualEyebrow}</p>
      <h3>{t.manualTitle}</h3>
      <p className="action-copy">{t.manualCopy}</p>
      <form className="manual-form" onSubmit={submitProposal}>
        <fieldset className="entry-type-fieldset">
          <legend>{t.manualTitle}</legend>
          <div className="entry-type-options">
            <label className={transactionType === 'income' ? 'entry-type is-selected' : 'entry-type'}>
              <input type="radio" name="transaction-type" value="income" checked={transactionType === 'income'} onChange={() => setTransactionType('income')} />
              <span>{t.incomeOption}</span>
            </label>
            <label className={transactionType === 'expense' ? 'entry-type is-selected' : 'entry-type'}>
              <input type="radio" name="transaction-type" value="expense" checked={transactionType === 'expense'} onChange={() => setTransactionType('expense')} />
              <span>{t.expenditureOption}</span>
            </label>
          </div>
        </fieldset>
        <label className="manual-field" htmlFor="manual-amount"><span>{t.amountLabel}</span><div className="amount-input"><span aria-hidden="true">₹</span><input id="manual-amount" type="number" min="0.01" step="0.01" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} required /></div></label>
        <label className="manual-field" htmlFor="manual-reason"><span>{t.reasonLabel}</span><textarea id="manual-reason" rows="2" maxLength="500" placeholder={t.reasonPlaceholder} value={reason} onChange={(event) => setReason(event.target.value)} required /></label>
        {error && <p className="manual-error" role="alert">{error}</p>}
        <button className="action-button terracotta-button manual-submit" type="submit" disabled={isBusy}>{isBusy ? '…' : t.submitEntry} <span aria-hidden="true">→</span></button>
      </form>
    </>}
  </article>
}

function ActionSection({ t, language, onSaved }) { return <section className="section-shell action-section" aria-labelledby="action-title"><div className="section-heading action-heading"><p className="eyebrow">{t.actionEyebrow}</p><h2 id="action-title">{t.actionTitle}</h2></div><div className="action-grid"><article className="action-card call-card"><div className="action-icon" aria-hidden="true">⌕</div><p className="eyebrow">{t.callEyebrow}</p><h3>{t.callTitle}</h3><p className="action-copy">{t.callCopy}</p><a className="action-button terracotta-button" href={`tel:${companionPhoneNumber}`}>{t.callButton} <span aria-hidden="true">→</span></a><p className="call-info">{t.voiceCallInfo} {companionPhoneNumber}</p></article><VoiceLogging t={t} language={language} onSaved={onSaved} /><ManualEntry t={t} onSaved={onSaved} /></div></section> }
function NextStep({ t, language, monthlySavings, goal }) {
  const target = Number(goal?.target_amount ?? 0)
  const current = Number(goal?.current_amount ?? 0)
  const remaining = Math.max(target - current, 0)
  const copy = dynamicNextStepCopy[language] || dynamicNextStepCopy.en
  return <section className="section-shell next-step" aria-labelledby="next-step-title"><div className="leaf-mark" aria-hidden="true">✳</div><div><p className="eyebrow">{t.nextEyebrow}</p><h2 id="next-step-title">{t.nextTitle}</h2><p>{copy({ savings: monthlySavings, remaining, goalName: goal?.name, hasGoal: Boolean(goal) })}</p></div><a className="arrow-link" href="#goal-title">{t.goalLink} <span aria-hidden="true">→</span></a></section>
}
function StorySection({ t, language }) {
  const [story, setStory] = useState(null)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const audioRef = useRef(null)
  const objectUrlRef = useRef(null)
  const playbackRef = useRef(0)

  const releaseAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.onended = null
      audioRef.current.onerror = null
      audioRef.current = null
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = null
    }
  }, [])

  useEffect(() => () => {
    playbackRef.current += 1
    releaseAudio()
  }, [releaseAudio])

  useEffect(() => {
    playbackRef.current += 1
    releaseAudio()
    setStory(null)
    setStatus('idle')
    setError('')
  }, [language, releaseAudio])

  const playStory = async (storyToPlay, playbackId) => {
    if (playbackId !== playbackRef.current) return
    setStatus('loading')
    setError('')
    try {
      const token = await getAccessToken()
      const narration = await narrateStory(storyToPlay.slug, language, token)
      if (playbackId !== playbackRef.current) return
      const binary = window.atob(narration.audio_base64)
      const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0))
      const objectUrl = URL.createObjectURL(new Blob([bytes], { type: narration.audio_mime_type }))
      releaseAudio()
      objectUrlRef.current = objectUrl
      const audio = new Audio(objectUrl)
      audioRef.current = audio
      audio.onended = () => {
        if (playbackId === playbackRef.current) setStatus('done')
      }
      audio.onerror = () => {
        if (playbackId === playbackRef.current) {
          setStatus('error')
          setError(t.storyError)
        }
      }
      await audio.play()
      if (playbackId === playbackRef.current) setStatus('playing')
    } catch (requestError) {
      if (playbackId === playbackRef.current) {
        setStatus('error')
        setError(requestError?.message || t.storyError)
      }
    }
  }

  const startStory = async () => {
    const playbackId = playbackRef.current + 1
    playbackRef.current = playbackId
    setError('')
    setStatus('loading')
    try {
      const token = await getAccessToken()
      const loadedStory = story || await getCurrentStory(language, token)
      if (playbackId !== playbackRef.current) return
      setStory(loadedStory)
      void playStory(loadedStory, playbackId)
    } catch (requestError) {
      if (playbackId === playbackRef.current) {
        setStatus('error')
        setError(requestError?.message || t.storyError)
      }
    }
  }

  const pauseStory = () => {
    if (audioRef.current && status === 'playing') {
      audioRef.current.pause()
      setStatus('paused')
    } else if (audioRef.current && status === 'paused') {
      void audioRef.current.play().then(() => setStatus('playing')).catch(() => setError(t.storyError))
    }
  }

  const actionLabel = status === 'loading' ? t.storyLoading : status === 'playing' ? t.storyPause : status === 'paused' ? t.storyContinue : status === 'done' ? t.storyAgain : t.storyButton
  const storyTranscript = story?.scenes?.map((scene) => scene.text).join(' ')
  return <section className="section-shell story-section" aria-labelledby="story-title"><div className="story-copy"><p className="eyebrow">{t.storyEyebrow}</p><h2 id="story-title">{t.storyTitle}</h2><p>{story?.story_summary || t.storyCopy}</p>{storyTranscript && <div className="story-scene" aria-live="polite"><span className="story-scene-label">{t.storyTextLabel}</span><p>{storyTranscript}</p></div>}{error && <p className="manual-error" role="alert">{error}</p>}<button className="story-button" type="button" disabled={status === 'loading'} onClick={status === 'playing' || status === 'paused' ? pauseStory : startStory}>{actionLabel} <span aria-hidden="true">{status === 'playing' ? 'Ⅱ' : '→'}</span></button></div><div className="story-motif" aria-hidden="true"><span className="motif-sun" /><span className="motif-stem" /><span className="motif-leaf motif-leaf-one" /><span className="motif-leaf motif-leaf-two" /><span className="motif-ground" /></div></section>
}
function Footer({ t }) { return <footer className="site-footer"><div className="footer-copy"><span className="brand-mark">{t.brand}</span><span>{t.footerCopy}</span></div><div className="footer-art"><WarliArt image={warliFooter} alt={t.footerAlt} /></div></footer> }

function AccountPanel({ t, profile, onProfileUpdated }) {
  const [phone, setPhone] = useState(profile.phone_number || '')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const save = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = await updateProfile({ phone_number: phone.trim() || null }, await getAccessToken())
      onProfileUpdated(result.profile)
      setMessage(t.confirmSaved)
    } catch (requestError) {
      setError(requestError?.message || t.authError)
    } finally {
      setBusy(false)
    }
  }

  return <section className="section-shell account-section" aria-labelledby="account-title"><div className="section-heading"><p className="eyebrow">{t.account}</p><h2 id="account-title">{profile.display_name || t.user}</h2></div><form className="account-form" onSubmit={save}><label className="manual-field" htmlFor="profile-phone"><span>{t.profilePhone}</span><input id="profile-phone" type="tel" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91…" /></label><button className="action-button terracotta-button" type="submit" disabled={busy}>{busy ? '…' : t.confirmSaved}</button>{message && <p className="auth-message" role="status">{message}</p>}{error && <p className="manual-error" role="alert">{error}</p>}</form><p className="call-info">{t.phoneRequired}</p></section>
}

function SignedInApp({ t, language, setLanguage, session, onSignOut, onProfileLanguage }) {
  const [profile, setProfile] = useState(null)
  const [financialContext, setFinancialContext] = useState(null)
  const [goals, setGoals] = useState([])
  const [transactions, setTransactions] = useState([])
  const [selectedGoalId, setSelectedGoalId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const initialLanguageSync = useRef(true)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setLoadError('')
    try {
      const token = session.access_token || await getAccessToken()
      const [me, context, goalList, transactionList] = await Promise.all([
        getCurrentUser(token), getFinancialContext(token), getGoals(token), getTransactions(token),
      ])
      setProfile(me.profile)
      setFinancialContext(context)
      setGoals(goalList)
      setTransactions(transactionList)
      if (initialLanguageSync.current) {
        initialLanguageSync.current = false
        if (languages.some((option) => option.code === me.profile.preferred_language) && me.profile.preferred_language !== language) onProfileLanguage(me.profile.preferred_language)
      }
    } catch (requestError) {
      setLoadError(requestError?.message || t.dashboardError)
    } finally {
      setLoading(false)
    }
  }, [language, onProfileLanguage, session.access_token, t.dashboardError])

  // The dashboard request synchronizes the signed-in session with remote state.
  // oxlint-disable-next-line react/set-state-in-effect
  useEffect(() => { void loadDashboard() }, [loadDashboard])

  if (loading) return <main className="loading-page"><p>{t.loading}</p></main>
  if (loadError || !profile) return <main className="loading-page"><p className="manual-error" role="alert">{loadError || t.loadError}</p><button className="action-button terracotta-button" type="button" onClick={() => void loadDashboard()}>{t.refresh}</button></main>
  if (!profile.onboarding_completed) return <OnboardingPanel t={t} language={language} setLanguage={setLanguage} profile={profile} onComplete={setProfile} />

  const signedInTranslations = { ...t, user: profile.display_name || t.user, avatar: (profile.display_name || t.avatar).slice(0, 1).toUpperCase() }
  const activeGoal = goals.find((goal) => goal.status === 'active') || goals[0]
  const selectedGoal = goals.find((goal) => goal.id === selectedGoalId)
  const visibleTransactions = transactions
  const isNewUser = visibleTransactions.length === 0 && goals.length === 0 && Number(financialContext?.total_income ?? 0) === 0 && Number(financialContext?.total_expenses ?? 0) === 0 && Number(financialContext?.current_savings ?? 0) === 0
  const monthlySavings = calculateMonthlySavings(visibleTransactions)
  return <div className="app"><Header t={signedInTranslations} language={language} setLanguage={setLanguage} onSignOut={onSignOut} /><main>{selectedGoal ? <GoalDetailsPage t={signedInTranslations} goal={selectedGoal} onBack={() => setSelectedGoalId(null)} onSaved={() => void loadDashboard()} /> : <><Hero t={signedInTranslations} userName={signedInTranslations.user} /><FinancialSnapshot t={signedInTranslations} financialContext={financialContext} />{isNewUser && <NewUserStart t={signedInTranslations} />}<GoalsSection t={signedInTranslations} goals={goals} onGoalsChanged={() => void loadDashboard()} onOpenGoal={(goal) => setSelectedGoalId(goal.id)} /><ActionSection t={signedInTranslations} language={language} onSaved={() => void loadDashboard()} /><ConversationPanel t={signedInTranslations} language={language} onSaved={() => void loadDashboard()} /><section className="section-shell transaction-section" aria-labelledby="transaction-title"><div className="section-heading"><p className="eyebrow">{signedInTranslations.transactionHistory}</p><h2 id="transaction-title">{signedInTranslations.transactionHistory}</h2></div>{visibleTransactions.length === 0 ? <p className="empty-copy">{signedInTranslations.noTransactions}</p> : <div className="transaction-list">{visibleTransactions.slice(0, 8).map((transaction) => <div className="transaction-row" key={transaction.id}><span>{transaction.description || (transaction.transaction_type === 'income' ? signedInTranslations.incomeRecorded : signedInTranslations.expenseRecorded)}</span><strong className={transaction.transaction_type === 'expense' ? 'expense-amount' : 'income-amount'}>{transaction.transaction_type === 'expense' ? '-' : '+'}{formatMoney(transaction.amount)}</strong><small>{transaction.date}{transaction.confirmation_status === 'confirmed' ? ` · ${signedInTranslations.confirmed}` : ''}</small></div>)}</div>}</section><NextStep t={signedInTranslations} language={language} monthlySavings={monthlySavings} goal={activeGoal} /><StorySection t={signedInTranslations} language={language} /><AccountPanel t={signedInTranslations} profile={profile} onProfileUpdated={setProfile} /></>}</main><Footer t={signedInTranslations} /></div>
}

function App() {
  const [language, setLanguage] = useState(() => {
    const selected = window.localStorage.getItem('sahachari.language-selected')
    return languages.some((option) => option.code === selected) ? selected : ''
  })
  const [languageReady, setLanguageReady] = useState(() => languages.some((option) => option.code === window.localStorage.getItem('sahachari.language-selected')))
  const activeLanguage = language || 'en'
  const t = { ...translations[activeLanguage], ...extraTranslations[activeLanguage], ...authFlowTranslations[activeLanguage], ...firstUserTranslations[activeLanguage], ...goalTranslations[activeLanguage], ...storyTranslations[activeLanguage], ...voiceFlowTranslations[activeLanguage] }
  const [session, setSession] = useState(() => (supabase ? undefined : null))

  const changeLanguage = useCallback((nextLanguage) => {
    setLanguage(nextLanguage)
    window.localStorage.setItem('sahachari.language', nextLanguage)
    window.localStorage.setItem('sahachari.language-selected', nextLanguage)
    if (supabase) {
      void getAccessToken().then((accessToken) => updatePreferredLanguage(nextLanguage, accessToken)).catch(() => {
        // A signed-out visitor can still use the local language preference.
      })
    }
  }, [])

  const chooseInitialLanguage = (nextLanguage) => {
    setLanguage(nextLanguage)
    window.localStorage.setItem('sahachari.language', nextLanguage)
    window.localStorage.setItem('sahachari.language-selected', nextLanguage)
    setLanguageReady(true)
  }

  useEffect(() => {
    if (!supabase) return undefined
    let active = true
    void supabase.auth.getSession().then(({ data }) => { if (active) setSession(data.session) })
    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => setSession(nextSession))
    return () => { active = false; listener.subscription.unsubscribe() }
  }, [])

  if (session === undefined) return <main className="loading-page"><p>{t.loading}</p></main>
  if (!languageReady) return <LanguageGate t={t} language={language} setLanguage={setLanguage} onContinue={() => chooseInitialLanguage(language)} />
  if (!session) return <AuthPanel t={t} language={language} setLanguage={changeLanguage} />
  return <SignedInApp t={t} language={language} setLanguage={changeLanguage} session={session} onSignOut={() => supabase?.auth.signOut()} onProfileLanguage={changeLanguage} />
}

export default App
