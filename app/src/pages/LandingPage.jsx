import { Link } from 'react-router-dom';
import InstallAppButton from '../components/InstallAppButton';

const highlights = [
  {
    title: 'See Where Money Goes',
    text: 'Get a clear view of your spending habits so you can make smarter daily decisions with confidence.',
  },
  {
    title: 'Stay in Control',
    text: 'Track bills, purchases, and recurring costs in one place to avoid surprises and protect your monthly goals.',
  },
  {
    title: 'Build Better Habits',
    text: 'Understand patterns over time and make small changes that create long-term financial stability.',
  },
];

const outcomes = [
  'Helps you to understand & reduce unnecessary spending with better day-to-day visibility',
  'Make faster budgeting decisions for family and personal goals',
  'Keep every expense organized and easy to understand',
  'Feel more confident during salary cycles and bill due dates',
];

export default function LandingPage() {
  return (
    <main className="landing-layout">
      <section className="landing-hero">
        <div className="landing-badge">Personal Finance Companion</div>
        <div className="landing-brand-row">
          <img
            src="/assets/FinTrackr_App_Logo-3.png"
            alt="FinTrackr icon"
            className="landing-brand-icon"
          />
          <img
            src="/assets/name_logo.svg"
            alt="FinTrackr"
            className="landing-brand-name"
          />
        </div>
        <h1>Manage money with clarity, confidence, and less stress.</h1>
        <p>
          FinTrackr helps individuals and families stay aware of spending,
          understand financial behavior, and make confident choices for everyday
          life and future plans.
        </p>
        <div className="landing-cta-row">
          <Link to="/register" className="landing-primary-cta">Get Started</Link>
          <Link to="/login" className="landing-secondary-cta">I Already Have an Account</Link>
          <InstallAppButton variant="hero" />
        </div>
      </section>

      <section className="landing-section">
        <h2>Why people choose FinTrackr</h2>
        <div className="landing-cards">
          {highlights.map((item) => (
            <article key={item.title} className="landing-card">
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section landing-outcomes">
        <h2>How it benefits you</h2>
        <ul>
          {outcomes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="landing-section landing-bottom-cta">
        <h2>Ready to take charge of your finances?</h2>
        <p>
          Start today and turn financial tracking into a simple habit that supports
          your goals.
        </p>
        <Link to="/register" className="landing-primary-cta">Create Free Account</Link>
      </section>
    </main>
  );
}
