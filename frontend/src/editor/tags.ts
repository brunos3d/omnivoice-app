export interface ModelTag {
  id: string;
  label: string;
  emoji: string;
  category: string;
  description: string;
  syntax: string;
}

/**
 * Fallback tag metadata used when the backend tag catalog isn't available yet.
 * Covers all tags from the built-in model catalog (Phase 4).
 */
export const FALLBACK_TAGS: ModelTag[] = [
  // Reactions
  { id: "laughter", label: "Laughter", emoji: "😂", category: "Reactions", description: "Adds laughter to the delivery", syntax: "[laughter]" },
  { id: "sigh", label: "Sigh", emoji: "😮‍💨", category: "Reactions", description: "A sighing exhale", syntax: "[sigh]" },

  // Confirmations
  { id: "confirmation-en", label: "Confirmation (EN)", emoji: "👍", category: "Confirmations", description: "English affirmative tone", syntax: "[confirmation-en]" },

  // Questions
  { id: "question-en", label: "Question (EN)", emoji: "❓", category: "Questions", description: "English question intonation", syntax: "[question-en]" },
  { id: "question-ah", label: "Question (Ah)", emoji: "❓", category: "Questions", description: "Question ending in 'ah'", syntax: "[question-ah]" },
  { id: "question-oh", label: "Question (Oh)", emoji: "❓", category: "Questions", description: "Question ending in 'oh'", syntax: "[question-oh]" },
  { id: "question-ei", label: "Question (Ei)", emoji: "❓", category: "Questions", description: "Question ending in 'ei'", syntax: "[question-ei]" },
  { id: "question-yi", label: "Question (Yi)", emoji: "❓", category: "Questions", description: "Question ending in 'yi'", syntax: "[question-yi]" },

  // Surprise
  { id: "surprise-ah", label: "Surprise (Ah)", emoji: "😲", category: "Surprise", description: "Surprised 'ah' exclamation", syntax: "[surprise-ah]" },
  { id: "surprise-oh", label: "Surprise (Oh)", emoji: "😲", category: "Surprise", description: "Surprised 'oh' exclamation", syntax: "[surprise-oh]" },
  { id: "surprise-wa", label: "Surprise (Wa)", emoji: "😲", category: "Surprise", description: "Surprised 'wa' exclamation", syntax: "[surprise-wa]" },
  { id: "surprise-yo", label: "Surprise (Yo)", emoji: "😲", category: "Surprise", description: "Surprised 'yo' exclamation", syntax: "[surprise-yo]" },

  // Dissatisfaction
  { id: "dissatisfaction-hnn", label: "Hmm", emoji: "😤", category: "Dissatisfaction", description: "Dissatisfied grunt", syntax: "[dissatisfaction-hnn]" },

  // Singing tags (omnivoice-singing)
  { id: "singing", label: "Singing", emoji: "🎤", category: "Vocal", description: "Sung delivery", syntax: "[singing]" },
  { id: "happy", label: "Happy", emoji: "😊", category: "Emotion", description: "Happy, cheerful delivery", syntax: "[happy]" },
  { id: "sad", label: "Sad", emoji: "😢", category: "Emotion", description: "Sad, melancholic delivery", syntax: "[sad]" },
  { id: "angry", label: "Angry", emoji: "😡", category: "Emotion", description: "Angry, intense delivery", syntax: "[angry]" },
  { id: "nervous", label: "Nervous", emoji: "😰", category: "Emotion", description: "Nervous, anxious delivery", syntax: "[nervous]" },
  { id: "whisper", label: "Whisper", emoji: "🤫", category: "Delivery", description: "Whispered delivery", syntax: "[whisper]" },
  { id: "calm", label: "Calm", emoji: "😌", category: "Delivery", description: "Calm, soothing delivery", syntax: "[calm]" },
  { id: "excited", label: "Excited", emoji: "🤩", category: "Emotion", description: "Excited, energetic delivery", syntax: "[excited]" },
];

export function tagById(id: string): ModelTag | undefined {
  return FALLBACK_TAGS.find((t) => t.id === id);
}

export function tagsByCategory(category: string): ModelTag[] {
  return FALLBACK_TAGS.filter((t) => t.category === category);
}

export function tagCategories(): string[] {
  return [...new Set(FALLBACK_TAGS.map((t) => t.category))];
}
