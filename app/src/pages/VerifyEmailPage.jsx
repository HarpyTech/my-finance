import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function VerifyEmailPage() {
  const { verifySignupOtp, resendSignupOtp } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialEmail = useMemo(() => searchParams.get('email') || '', [searchParams]);

  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);

  async function handleVerify(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setVerifying(true);

    try {
      await verifySignupOtp(email, otp);
      navigate('/login');
    } catch (err) {
      setError(err.message);
    } finally {
      setVerifying(false);
    }
  }

  async function handleResendOtp() {
    if (!email) {
      setError('Please enter your email first.');
      return;
    }

    setError('');
    setMessage('');
    setResending(true);

    try {
      await resendSignupOtp(email);
      setMessage('A new OTP has been sent to your email.');
    } catch (err) {
      setError(err.message);
    } finally {
      setResending(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-card">
        <h1>Verify your account</h1>
        <p>
          Enter the OTP sent to your email to activate your account and complete login.
        </p>
        <form onSubmit={handleVerify} className="stack-form">
          <label>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
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
          <button disabled={verifying} type="submit">
            {verifying ? 'Verifying...' : 'Verify account'}
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={resending}
            onClick={handleResendOtp}
          >
            {resending ? 'Resending OTP...' : 'Resend OTP'}
          </button>
        </form>
        <p>
          Remembered your password? <Link to="/login">Back to sign in</Link>
        </p>
      </section>
    </main>
  );
}
