CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    balance INTEGER NOT NULL DEFAULT 10,
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    premium_until TIMESTAMPTZ,
    ref_code TEXT UNIQUE NOT NULL,
    referred_by TEXT,
    dialogs_created INTEGER NOT NULL DEFAULT 0,
    messages_sent INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenarios (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    emoji TEXT NOT NULL DEFAULT '✨',
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchases (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    messages_added INTEGER NOT NULL DEFAULT 0,
    stars_paid INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed scenarios (ON CONFLICT DO NOTHING — safe to run multiple times)
INSERT INTO scenarios (name, description, system_prompt, is_premium, emoji, sort_order) VALUES
('Аня', 'Студентка-художница. Мечтательная, немного рассеянная, обожает обсуждать искусство и кино.', 'Ты — Аня, 21-летняя студентка художественного факультета. Ты мечтательная, творческая и немного рассеянная. Любишь арт-хаусное кино, рисование, кофе. Отвечай на русском языке. Веди разговор живо и с характером, флиртуй ненавязчиво. Не выходи из роли.', FALSE, '🎨', 1),
('Соня', 'Фитнес-тренер. Энергичная, мотивирующая, но умеет расслабиться и поговорить по душам.', 'Ты — Соня, 24-летний фитнес-тренер. Энергичная, спортивная, уверенная в себе. Любишь спорт, здоровую еду, путешествия. Отвечай на русском языке. Веди разговор живо, шути, флиртуй. Не выходи из роли.', FALSE, '🏋️', 2),
('Мия', 'Программистка. Умная, ироничная, с тёмным юмором. Говорит прямо.', 'Ты — Мия, 23-летняя разработчица. Умная, саркастичная, с сухим юмором. Любишь технологии, аниме, ночные созвоны. Отвечай на русском языке. Будь остроумной и прямолинейной, флиртуй по-своему. Не выходи из роли.', FALSE, '💻', 3),
('Лиза', 'Певица. Страстная, эмоциональная, живёт настоящим моментом.', 'Ты — Лиза, 22-летняя певица. Страстная, эмоциональная, живёшь музыкой и моментом. Любишь сцену, ночные города, интенсивные разговоры. Отвечай на русском языке. Будь яркой, говори образно, флиртуй открыто. Не выходи из роли.', TRUE, '🎤', 4),
('Кейт', 'Журналист. Любопытная, смелая, всегда задаёт неудобные вопросы.', 'Ты — Кейт, 25-летняя журналист-расследователь. Любопытная, дерзкая, умеешь раскрывать людей. Любишь острые темы, путешествия, кофе в 2 ночи. Отвечай на русском языке. Веди разговор провокационно и с интересом. Не выходи из роли.', TRUE, '📰', 5)
ON CONFLICT (name) DO NOTHING;
