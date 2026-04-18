import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(form.username, form.password);
      navigate('/dashboard');
    } catch (err) {
      if ((err.message || '').toLowerCase().includes('email not verified')) {
        const encodedEmail = encodeURIComponent(form.username);
        navigate(`/verify-email?email=${encodedEmail}`);
        return;
      }
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-card">
        <h1>Welcome back</h1>
        <p>Sign in to track daily expenses and monitor monthly and yearly trends.</p>
        <form onSubmit={handleSubmit} className="stack-form">
          <label>
            Email
            <input
              type="email"
              required
              value={form.username}
              onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button disabled={submitting} type="submit">
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p>
          New user? <Link to="/register">Create an account</Link>
        </p>
        <p>
          Already registered but not verified? <Link to="/verify-email">Verify now</Link>
        </p>
      </section>
    </main>
  );
}
