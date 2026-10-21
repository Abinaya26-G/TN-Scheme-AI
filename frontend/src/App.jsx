
import { useState, useRef, useEffect } from "react";
import "./App.css";

const suggestions = [
  {
    icon: "🎓",
    title: "Education schemes",
    question:
      "What education schemes are available for students in Tamil Nadu?",
  },
  {
    icon: "👩‍🎓",
    title: "Pudhumai Penn",
    question: "What is the Pudhumai Penn Scheme and who is eligible?",
  },
  {
    icon: "📋",
    title: "Eligibility & documents",
    question:
      "What documents are required to apply for government schemes?",
  },
  {
    icon: "💰",
    title: "Financial assistance",
    question:
      "What financial assistance schemes are available for students?",
  },
];

function App() {
  // Chat state
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Authentication state
  const [authMode, setAuthMode] = useState("login");
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authConfirmPassword, setAuthConfirmPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  const [token, setToken] = useState(
    () => localStorage.getItem("schemeai_token") || ""
  );

  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(
        localStorage.getItem("schemeai_user") || "null"
      );
    } catch {
      return null;
    }
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Register and login
  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthError("");
    setAuthSuccess("");

    const isRegister = authMode === "register";

    if (isRegister && authPassword !== authConfirmPassword) {
      setAuthError("Passwords do not match.");
      return;
    }

    setAuthLoading(true);

    try {
      const response = await fetch(
        isRegister ? "/api/auth/register" : "/api/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(
            isRegister
              ? {
                  name: authName.trim(),
                  email: authEmail.trim(),
                  password: authPassword,
                }
              : {
                  email: authEmail.trim(),
                  password: authPassword,
                }
          ),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Authentication failed. Please try again."
        );
      }

      if (isRegister) {
        setAuthMode("login");
        setAuthName("");
        setAuthPassword("");
        setAuthConfirmPassword("");
        setAuthSuccess(
          "Registration successful! Please log in with your account."
        );
      } else {
        if (!data.access_token || !data.user) {
          throw new Error("The server returned an invalid login response.");
        }

        localStorage.setItem("schemeai_token", data.access_token);
        localStorage.setItem(
          "schemeai_user",
          JSON.stringify(data.user)
        );

        setToken(data.access_token);
        setCurrentUser(data.user);
        setAuthPassword("");
        setAuthConfirmPassword("");
        setMessages([]);
        setQuestion("");
        setError("");
      }
    } catch (err) {
      setAuthError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the backend. Check FastAPI and Vite."
          : err.message
      );
    } finally {
      setAuthLoading(false);
    }
  }

  function switchAuthMode(mode) {
    setAuthMode(mode);
    setAuthError("");
    setAuthSuccess("");
    setAuthPassword("");
    setAuthConfirmPassword("");
  }

  function handleLogout() {
    localStorage.removeItem("schemeai_token");
    localStorage.removeItem("schemeai_user");

    setToken("");
    setCurrentUser(null);
    setMessages([]);
    setQuestion("");
    setError("");
    setAuthError("");
    setAuthSuccess("");
    setAuthEmail("");
    setAuthPassword("");
    setAuthMode("login");
  }

  // Existing chatbot
  async function sendQuestion(text = question) {
    const value = text.trim();

    if (!value || loading) return;

    setQuestion("");
    setError("");

    setMessages((previous) => [
      ...previous,
      { role: "user", text: value },
    ]);

    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: value }),
      });

      const data = await response.json();

      if (response.status === 401 || response.status === 403) {
        handleLogout();
        throw new Error(
          "Your session has expired or access was denied. Please log in again."
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to get an answer. Please try again."
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: data.answer || "No answer was returned.",
          sources: Array.isArray(data.sources) ? data.sources : [],
        },
      ]);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the backend. Please check whether FastAPI is running."
          : err.message
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function startNewChat() {
    if (loading) return;

    setMessages([]);
    setQuestion("");
    setError("");
    inputRef.current?.focus();
  }

  // Login screen appears first
  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">TN</div>

          <h1>
            Scheme<span>AI</span>
          </h1>

          <p className="auth-subtitle">
            Your Tamil Nadu Government Scheme Assistant
          </p>

          <h2>
            {authMode === "login"
              ? "Welcome back!"
              : "Create your account"}
          </h2>

          <p className="auth-description">
            {authMode === "login"
              ? "Login to continue to SchemeAI."
              : "Register to get started with SchemeAI."}
          </p>

          {authError && (
            <div className="auth-error" role="alert">
              {authError}
            </div>
          )}

          {authSuccess && (
            <div className="auth-success" role="status">
              {authSuccess}
            </div>
          )}

          <form className="auth-form" onSubmit={handleAuthSubmit}>
            {authMode === "register" && (
              <label>
                Full name
                <input
                  type="text"
                  placeholder="Enter your name"
                  value={authName}
                  onChange={(event) => setAuthName(event.target.value)}
                  minLength={2}
                  maxLength={100}
                  autoComplete="name"
                  required
                />
              </label>
            )}

            <label>
              Email address
              <input
                type="email"
                placeholder="you@example.com"
                value={authEmail}
                onChange={(event) => setAuthEmail(event.target.value)}
                maxLength={254}
                autoComplete="email"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                placeholder="Enter your password"
                value={authPassword}
                onChange={(event) =>
                  setAuthPassword(event.target.value)
                }
                minLength={authMode === "register" ? 8 : 1}
                maxLength={128}
                autoComplete={
                  authMode === "login"
                    ? "current-password"
                    : "new-password"
                }
                required
              />
            </label>

            {authMode === "register" && (
              <label>
                Confirm password
                <input
                  type="password"
                  placeholder="Re-enter your password"
                  value={authConfirmPassword}
                  onChange={(event) =>
                    setAuthConfirmPassword(event.target.value)
                  }
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  required
                />
              </label>
            )}

            <button
              className="auth-submit"
              type="submit"
              disabled={authLoading}
            >
              {authLoading
                ? "Please wait..."
                : authMode === "login"
                  ? "Login"
                  : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            {authMode === "login"
              ? "Don't have an account?"
              : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() =>
                switchAuthMode(
                  authMode === "login" ? "register" : "login"
                )
              }
            >
              {authMode === "login" ? "Register" : "Login"}
            </button>
          </p>
        </div>
      </div>
    );
  }

  // Existing SchemeAI chatbot dashboard
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">TN</div>
          <div>
            <h2>
              Scheme<span>AI</span>
            </h2>
            <p>Citizen assistance</p>
          </div>
        </div>

        <button className="new-chat" onClick={startNewChat}>
          <span>＋</span> New conversation
        </button>

        <div className="sidebar-label">EXPLORE</div>

        <button
          className="side-link"
          onClick={() =>
            sendQuestion(
              "What government schemes are available in Tamil Nadu?"
            )
          }
        >
          <span>◈</span> All schemes
        </button>

        <button
          className="side-link"
          onClick={() =>
            sendQuestion(
              "What education schemes are available for students in Tamil Nadu?"
            )
          }
        >
          <span>▤</span> Education
        </button>

        <button
          className="side-link"
          onClick={() =>
            sendQuestion(
              "What women welfare schemes are available in Tamil Nadu?"
            )
          }
        >
          <span>♡</span> Women welfare
        </button>

        <button
          className="side-link"
          onClick={() =>
            sendQuestion(
              "What farmer welfare schemes are available in Tamil Nadu?"
            )
          }
        >
          <span>♧</span> Farmers
        </button>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>AI Assistant</strong>
            <p>Government scheme information</p>
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="mobile-brand">
            <div className="brand-icon small">TN</div>
            <strong>SchemeAI</strong>
          </div>

          <div className="breadcrumb">
            Tamil Nadu <span>/</span> Scheme Assistant
          </div>

          <div className="topbar-actions">
            {currentUser && (
              <span className="user-greeting">
                Hi, {currentUser.name}
              </span>
            )}

            <div className="online-status">
              <span /> AI Assistant
            </div>

            <button
              className="logout-button"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </header>

        <section
          className={`chat-area ${
            messages.length === 0 ? "welcome-mode" : ""
          }`}
        >
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-emblem">✦</div>
              <div className="eyebrow">
                YOUR GOVERNMENT SCHEME GUIDE
              </div>

              <h1>
                How can we help
                <br />
                you <span>today?</span>
              </h1>

              <p className="welcome-description">
                Discover Tamil Nadu government schemes, understand
                eligibility, and explore benefits using a simple
                AI-powered assistant.
              </p>

              <div className="suggestion-grid">
                {suggestions.map((item) => (
                  <button
                    className="suggestion-card"
                    key={item.title}
                    onClick={() => sendQuestion(item.question)}
                    disabled={loading}
                  >
                    <span className="suggestion-icon">
                      {item.icon}
                    </span>
                    <strong>{item.title}</strong>
                    <span className="suggestion-question">
                      {item.question}
                    </span>
                    <span className="card-arrow">↗</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="conversation">
              <div className="conversation-heading">
                <div>
                  <div className="eyebrow">YOUR CONVERSATION</div>
                  <h2>Scheme Assistant</h2>
                </div>

                <span className="message-count">
                  {messages.filter((m) => m.role === "user").length}{" "}
                  questions
                </span>
              </div>

              {messages.map((message, index) => (
                <div
                  className={`message-row ${message.role}`}
                  key={`${index}-${message.role}`}
                >
                  {message.role === "assistant" && (
                    <div className="avatar">✦</div>
                  )}

                  <div className="message-content">
                    {message.role === "assistant" && (
                      <div className="message-label">
                        SchemeAI Assistant
                      </div>
                    )}

                    <div className="message-bubble">
                      {message.text}
                    </div>

                    {message.sources?.length > 0 && (
                      <div className="sources">
                        <strong>↗ Sources &amp; references</strong>

                        {message.sources.map((source, i) => {
                          let validUrl;

                          try {
                            validUrl = new URL(source);
                          } catch {
                            validUrl = null;
                          }

                          if (
                            !validUrl ||
                            !["https:", "http:"].includes(
                              validUrl.protocol
                            )
                          ) {
                            return (
                              <div className="source-link" key={i}>
                                {source}
                              </div>
                            );
                          }

                          return (
                            <a
                              className="source-link"
                              href={validUrl.href}
                              target="_blank"
                              rel="noopener noreferrer"
                              key={i}
                            >
                              <span>{validUrl.hostname}</span>
                              <span>↗</span>
                            </a>
                          );
                        })}

                        <p className="source-note">
                          Verify scheme details with the relevant
                          official department.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row assistant">
                  <div className="avatar">✦</div>

                  <div className="message-content">
                    <div className="message-label">
                      SchemeAI Assistant
                    </div>

                    <div className="message-bubble typing-bubble">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-text">
                        Finding relevant information...
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}

          {error && (
            <div className="error-banner" role="alert">
              <span>⚠</span>
              <div>{error}</div>
              <button
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          )}
        </section>

        <footer className="composer-area">
          <form
            className="composer"
            onSubmit={(event) => {
              event.preventDefault();
              sendQuestion();
            }}
          >
            <textarea
              ref={inputRef}
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  sendQuestion();
                }
              }}
              placeholder="Ask anything about Tamil Nadu government schemes..."
              rows={2}
              maxLength={1000}
              disabled={loading}
              aria-label="Your question"
            />

            <div className="composer-bottom">
              <span className="input-hint">
                ↵ Send · Shift + ↵ New line
              </span>

              <div className="send-group">
                <span className="character-count">
                  {question.length}/1000
                </span>

                <button
                  className="send-button"
                  type="submit"
                  disabled={!question.trim() || loading}
                  aria-label="Send question"
                >
                  {loading ? "…" : "↑"}
                </button>
              </div>
            </div>
          </form>

          <p className="disclaimer">
            AI-generated responses may be incomplete. Confirm
            important details with official sources.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
