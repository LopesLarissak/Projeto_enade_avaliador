import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function highlightedText(fragment) {
  if (!fragment) return null;
  return fragment.split(/(<em>[\s\S]*?<\/em>)/gi).map((part, index) => {
    const match = part.match(/^<em>([\s\S]*)<\/em>$/i);
    return match
      ? <mark key={index}>{match[1]}</mark>
      : <span key={index}>{part}</span>;
  });
}

function App() {
  const [query, setQuery] = useState('');
  const [area, setArea] = useState('');
  const [course, setCourse] = useState('');
  const [year, setYear] = useState('');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(null);
  const [error, setError] = useState('');
  const [loginError, setLoginError] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [profile, setProfile] = useState(null);

  async function login(event) {
    event.preventDefault();
    setLoginError('');
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error('Não foi possível autenticar.');
      const data = await response.json();
      setToken(data.access_token);
      setProfile(data.user);
      setPassword('');
    } catch {
      setLoginError('Login indisponível. Confira os serviços e o usuário LDAP.');
    }
  }

  async function search(event) {
    event.preventDefault();
    setError('');
    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());
    if (area.trim()) params.set('area', area.trim());
    if (course.trim()) params.set('course', course.trim());
    if (year.trim()) params.set('year', year.trim());

    try {
      const response = await fetch(`${API_BASE}/questions?${params.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) throw new Error('Falha na consulta.');
      const data = await response.json();
      setItems(data.items || []);
      setTotal(data.total ?? 0);
    } catch {
      setError('Não foi possível consultar. Verifique se a API e os serviços estão ativos.');
    }
  }

  function logout() {
    setToken('');
    setProfile(null);
    setPassword('');
  }

  return (
    <main>
      <header className="topbar">
        <div>
          <p className="eyebrow">ENADE AVALIADOR</p>
          <h1>Acervo de questões</h1>
          <p className="intro">
            Busque por assunto em diferentes áreas e cursos; professores podem acessar
            recursos conforme o perfil LDAP.
          </p>
        </div>
        {profile ? (
          <div className="profile">
            <span>{profile.username}</span>
            <strong>{profile.role}</strong>
            <button className="secondary" onClick={logout} type="button">Sair</button>
          </div>
        ) : (
          <form className="login" onSubmit={login}>
            <label>
              Usuário LDAP
              <input value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <button type="submit">Entrar</button>
            {loginError && <p className="error" role="alert">{loginError}</p>}
          </form>
        )}
      </header>

      <section className="search-panel" aria-label="Busca de questões">
        <form onSubmit={search}>
          <label className="query-field">
            Tema, competência ou enunciado
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ex.: ética, sustentabilidade, tecnologia"
            />
          </label>
          <div className="filters">
            <label>
              Área
              <input
                value={area}
                onChange={(event) => setArea(event.target.value)}
                placeholder="Computação"
              />
            </label>
            <label>
              Curso
              <input value={course} onChange={(event) => setCourse(event.target.value)} />
            </label>
            <label>
              Ano
              <input
                inputMode="numeric"
                value={year}
                onChange={(event) => setYear(event.target.value)}
                placeholder="2021"
              />
            </label>
            <button type="submit">Buscar questões</button>
          </div>
        </form>
        <p className="hint">
          A busca textual consulta enunciados e alternativas; mais de uma área pode ser
          filtrada ao mesmo tempo.
        </p>
      </section>

      {error && <p className="error" role="alert">{error}</p>}
      {total !== null && <p className="result-count">{total} resultado(s)</p>}
      <section className="results" aria-live="polite">
        {items.map((item) => {
          const highlighted = item.highlight?.statement?.[0];
          return (
            <article key={item.id}>
              <small>
                {item.question.area || 'Área não identificada'} ·{' '}
                {item.question.course || 'Curso não informado'} ·{' '}
                {item.question.year || 'Ano não informado'} ·{' '}
                {item.question.source_pdf}, pág. {item.question.source_page}
              </small>
              <p>
                {highlighted
                  ? highlightedText(highlighted)
                  : item.question.statement}
              </p>
              {item.question.answer_key && (
                <p className="answer">
                  Gabarito: <strong>{item.question.answer_key}</strong>
                </p>
              )}
            </article>
          );
        })}
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
