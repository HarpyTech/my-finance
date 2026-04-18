import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function RegisterPage() {
  const { requestSignupOtp, verifySignupOtp } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '', confirmPassword: '' });
  const [otp, setOtp] = useState('');
  const [otpStep, setOtpStep] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleRequestOtp(event) {
    event.preventDefault();
    setError('');
    setMessage('');

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setSubmitting(true);
    try {
      await requestSignupOtp(form.username, form.password);
      setOtpStep(true);
      setMessage('Verification OTP sent to your email. Enter it below to activate your account.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyOtp(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setSubmitting(true);

    try {
      await verifySignupOtp(form.username, otp);
      navigate('/login');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-card">
        <h1>Create your account</h1>
        <p>Start logging your expenses and get monthly/yearly insights instantly.</p>
        {!otpStep ? (
          <form onSubmit={handleRequestOtp} className="stack-form">
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
                minLength={8}
                required
                value={form.password}
                onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
              />
            </label>
            <label>
              Confirm Password
              <input
                type="password"
                minLength={8}
                required
                value={form.confirmPassword}
                onChange={(e) => setForm((prev) => ({ ...prev, confirmPassword: e.target.value }))}
              />
            </label>
            {message ? <p>{message}</p> : null}
            {error ? <p className="error-text">{error}</p> : null}
            <button disabled={submitting} type="submit">
              {submitting ? 'Sending OTP...' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="stack-form">
            <label>
              Email
              <input type="email" value={form.username} disabled />
            </label>
            <label>
              OTP
              <input
                type="text"
                inputMode="numeric"
                maxLength={8}
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              />
            </label>
            {message ? <p>{message}</p> : null}
            {error ? <p className="error-text">{error}</p> : null}
            <button disabled={submitting} type="submit">
              {submitting ? 'Verifying OTP...' : 'Verify & Create Account'}
            </button>
          </form>
        )}
        <p>
          Already registered? <Link to="/login">Sign in</Link>
        </p>
        <p>
          Need to verify later? <Link to="/verify-email">Verify account</Link>
        </p>
      </section>
    </main>
  );
}
