import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useAuthorizedEmails, isAuthorizedEmail } from '../../config/emailAuth';
import { ROLES } from '../../config/roles';
import styles from './EmailLogin.module.css';

export default function EmailLogin() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const authorizedEmails = useAuthorizedEmails();

  const handleSubmit = (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Enter a valid email address.');
      setLoading(false);
      return;
    }

    const hasTechnicalAccess = isAuthorizedEmail(trimmedEmail, authorizedEmails);

    login(
      {
        email: trimmedEmail,
        username: trimmedEmail,
        name: trimmedEmail.split('@')[0],
      },
      hasTechnicalAccess ? ROLES.CAMPUS_ADMIN : ROLES.STUDENT
    );

    setLoading(false);
  };

  return (
    <main className={styles.loginContainer}>
      <section className={styles.loginPanel} aria-labelledby="doc-login-title">
        <p className={styles.eyebrow}>Aura Documentation</p>
        <h1 id="doc-login-title">Sign in to continue</h1>
        <p className={styles.subtitle}>
          Use your school email. Authorized staff emails unlock technical documentation; other emails open the user guides.
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label htmlFor="doc-email" className={styles.label}>
            Email address
          </label>
          <input
            id="doc-email"
            type="email"
            placeholder="name@school.edu"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setError('');
            }}
            className={styles.emailInput}
            required
            disabled={loading}
            autoFocus
          />

          {error ? <div className={styles.error}>{error}</div> : null}

          <button type="submit" className={styles.loginButton} disabled={loading}>
            {loading ? 'Checking access...' : 'Continue'}
          </button>
        </form>

        <div className={styles.accessNotes}>
          <p>
            <strong>User guides:</strong> students, SSG, SG, ORG, campus staff, and admins.
          </p>
          <p>
            <strong>Technical docs:</strong> admin, campus admin, school IT, or authorized email only.
          </p>
        </div>
      </section>
    </main>
  );
}
