const SUPPORTED_LANGUAGES = new Set(['en', 'hi', 'te'])

const amountPattern = /(?:₹|rs\.?|inr|rupees?|रुप(?:ये|ए)?|రూపాయ(?:లు|ల)?)?\s*([0-9][0-9,]*(?:\.\d+)?)/iu

const numberWords = {
  en: {
    zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
    eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19,
    twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90,
    hundred: 100, thousand: 1000, lakh: 100000, lakhs: 100000,
  },
  hi: {
    शून्य: 0, एक: 1, दो: 2, तीन: 3, चार: 4, पाँच: 5, पांच: 5, छह: 6, छः: 6, सात: 7, आठ: 8, नौ: 9, दस: 10,
    ग्यारह: 11, बारह: 12, तेरह: 13, चौदह: 14, पंद्रह: 15, पन्द्रह: 15, सोलह: 16, सत्रह: 17, अठारह: 18, उन्नीस: 19,
    बीस: 20, तीस: 30, चालीस: 40, पचास: 50, साठ: 60, सत्तर: 70, अस्सी: 80, नब्बे: 90,
    सौ: 100, सैकड़ा: 100, हजार: 1000, हज़ार: 1000, लाख: 100000,
  },
  te: {
    సున్నా: 0, ఒకటి: 1, ఒక: 1, రెండు: 2, మూడు: 3, నాలుగు: 4, ఐదు: 5, అయిదు: 5, ఆరు: 6, ఏడు: 7, ఎనిమిది: 8, తొమ్మిది: 9, పది: 10,
    పదకొండు: 11, పన్నెండు: 12, పదమూడు: 13, పద్నాలుగు: 14, పదిహేను: 15, పదహారు: 16, పదిహేడు: 17, పద్దెనిమిది: 18, పంతొమ్మిది: 19,
    ఇరవై: 20, ముప్పై: 30, నలభై: 40, యాభై: 50, అరవై: 60, డెబ్బై: 70, ఎనభై: 80, తొంభై: 90,
    వంద: 100, వందలు: 100, వందల: 100, వెయ్యి: 1000, వేలు: 1000, లక్ష: 100000, లక్షలు: 100000,
  },
}

const typeTerms = {
  expense: /(?:spent|spend|paid|pay|bought|buy|purchased|expense|cost|खर्च|खरीद|भुगतान|खरीदा|చెల్లించ|ఖర్చు|కొన్న|కొనుగోలు|వ్యయం)/iu,
  income: /(?:received|receive|earned|earn|got paid|salary|wages|income|మిలింది|వచ్చింది|వచ్చాయి|సంపాదించ|ఆదాయం|జీతం|కూలి|मिला|मिले|मिली|कमाया|कमाई|आमदनी|आय|वेतन|मजदूरी)/iu,
}

function cleanText(value) {
  return String(value || '').replace(/[!?;,]+/g, ' ').replace(/\s+/g, ' ').trim()
}

function numberFromWords(value) {
  const source = cleanText(value).toLowerCase().replace(/-/g, ' ')
  const tokens = source.split(/\s+/).filter(Boolean)
  const dictionaries = Object.values(numberWords)
  const values = tokens.map((token) => dictionaries.find((dictionary) => dictionary[token])?.[token])
  if (!values.length || values.some((number) => number === undefined)) return null

  let total = 0
  let current = 0
  for (const number of values) {
    if (number === 100 || number === 1000 || number === 100000) {
      current = (current || 1) * number
      if (number >= 1000) {
        total += current
        current = 0
      }
    } else {
      current += number
    }
  }
  return total + current || null
}

function extractAmount(text) {
  const source = cleanText(text)
  const match = source.match(amountPattern)
  if (match) {
    const amount = Number(match[1].replace(/,/g, ''))
    if (Number.isFinite(amount) && amount > 0) return { amount, raw: match[0] }
  }

  const wordTokens = source
    .toLowerCase()
    .replace(/[.,!?;]+/g, ' ')
    .split(/\s+/)
    .filter((token) => Object.values(numberWords).some((dictionary) => Object.prototype.hasOwnProperty.call(dictionary, token)))
  if (wordTokens.length) {
    const amount = numberFromWords(wordTokens.join(' '))
    if (amount) return { amount, raw: wordTokens.join(' ') }
  }
  return { amount: null, raw: '' }
}

function detectTransactionType(text) {
  const value = cleanText(text)
  if (typeTerms.expense.test(value)) return 'expense'
  if (typeTerms.income.test(value)) return 'income'
  return null
}

function removeKnownWords(value, amountRaw) {
  let result = cleanText(value)
  if (amountRaw) result = result.replace(amountRaw, ' ')
  result = result.replace(/₹|rs\.?|inr|rupees?|रुप(?:ये|ए)?|రూపాయ(?:లు|ల)?/giu, ' ')
  result = result.replace(/\b(i|me|my|we|our|today|yesterday|please|spent|spend|paid|pay|bought|buy|purchased|expense|cost|received|receive|earned|earn|got|from|on|for|of|towards|the|a|an|no|it|was|actually|instead|only|this)\b/giu, ' ')
  result = result.replace(/\b(ki|ke|liye|se|par|ko|ka|keliye|chesanu|chesthanu|chesa|చేశాను|చేసాను|చేశా|చేస్తాను|కోసం|నుంచి|కు|తో|కి|లో|గురించి)\b/giu, ' ')
  result = result.replace(/(?:^|\s)(मैंने|मैं|मुझे|मेरी|आज|कल|के|लिए|पर|से|खर्च|खरीदा|खरीद|भुगतान|मिला|मिले|मिली|कमाया|आमदनी|आय|वेतन|नहीं|गलत|किए|నిన్న|ఈరోజు|ఈ రోజు|నేను|నాకు|ఖర్చు|కొన్నాను|కొనుగోలు|చెల్లించాను|వచ్చింది|వచ్చాయి|సంపాదించాను|ఆదాయం|జీతం|కూలి|కాదు|తప్పు|లేదు|చేశాను|చేసాను|చేశా|కోసం|నుంచి|కు|తో|కి)(?=\s|$)/giu, ' ')
  return result.replace(/[,.]/g, ' ').replace(/\s+/g, ' ').replace(/(?:లకు|లకోసం|కోసం|కి|కు)$/u, '').trim()
}

function extractPurpose(text, amountRaw) {
  const value = cleanText(text)
  const afterConnector = value.match(/(?:\b(?:on|for|from|towards|at|to)\b|के लिए|से|पर|के|కోసం|నుంచి|కు|తో|కి|\b(?:ki|ke liye|se)\b)\s+(.+)$/iu)
  if (afterConnector?.[1]) {
    const purpose = removeKnownWords(afterConnector[1], amountRaw).replace(/(?:లకు|లకోసం|కోసం|కి|కు)$/u, '').trim()
    if (purpose && !/^\d/.test(purpose)) return purpose
  }

  // Telugu/Hinglish frequently places the purpose before “ki/కు/కి”.
  const beforeConnector = value.match(/^(.+?)\s+(?:ki|కు|కి|కోసం|లకోసం|లకు)\s+.+$/iu)
  if (beforeConnector?.[1]) {
    const purpose = removeKnownWords(beforeConnector[1], amountRaw).replace(/(?:లకు|లకోసం|కోసం|కి|కు)$/u, '').trim()
    if (purpose) return purpose
  }

  const purpose = removeKnownWords(value, amountRaw).replace(/(?:లకు|లకోసం|కోసం|కి|కు)$/u, '').trim()
  return purpose && !/^\d/.test(purpose) ? purpose : null
}

export function parseVoiceTransaction(text) {
  const source = cleanText(text)
  const { amount, raw: amountRaw } = extractAmount(source)
  const transactionType = detectTransactionType(source)
  const purpose = isConfirmation(source) || isRejection(source) ? null : extractPurpose(source, amountRaw)
  return {
    transaction_type: transactionType,
    amount,
    purpose: purpose || null,
    confirmation_status: 'not_confirmed',
    missing: [
      !transactionType && 'transaction_type',
      !amount && 'amount',
      !purpose && 'purpose',
    ].filter(Boolean),
  }
}

export function mergeVoiceTransaction(draft, text) {
  const parsed = parseVoiceTransaction(text)
  const transaction = {
    transaction_type: parsed.transaction_type || draft?.transaction_type || null,
    amount: parsed.amount || draft?.amount || null,
    purpose: parsed.purpose || draft?.purpose || null,
    confirmation_status: 'not_confirmed',
  }
  return {
    ...transaction,
    missing: [
      !transaction.transaction_type && 'transaction_type',
      !transaction.amount && 'amount',
      !transaction.purpose && 'purpose',
    ].filter(Boolean),
  }
}

export function isConfirmation(text) {
  return /^(yes|yeah|yep|correct|right|that's right|that is right|confirm|confirmed|record it|అవును|అవునండి|సరైనదే|సరే|నమోదు చేయండి|हाँ|हां|सही है|ठीक है|दर्ज करें)(?:\s+please)?[.!,\s]*$/iu.test(cleanText(text))
}

export function isRejection(text) {
  return /^(no|nope|wrong|not correct|change|కాదు|తప్పు|లేదు|మార్చండి|नहीं|गलत|बदलें|नही)\b/iu.test(cleanText(text))
}

export function describeVoiceTransaction(transaction, language = 'en') {
  const amount = `₹${new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(transaction.amount)}`
  if (language === 'te') return transaction.transaction_type === 'income' ? `${amount} ${transaction.purpose} నుండి వచ్చాయి. ఇది సరైనదేనా?` : `${amount} ${transaction.purpose} కోసం ఖర్చు చేశారు. ఇది సరైనదేనా?`
  if (language === 'hi') return transaction.transaction_type === 'income' ? `${amount} ${transaction.purpose} से मिले। क्या यह सही है?` : `${amount} ${transaction.purpose} पर खर्च हुए। क्या यह सही है?`
  return transaction.transaction_type === 'income' ? `You received ${amount} from ${transaction.purpose}. Is that correct?` : `You spent ${amount} on ${transaction.purpose}. Is that correct?`
}

export function isSupportedVoiceLanguage(language) {
  return SUPPORTED_LANGUAGES.has(language)
}
