import React from 'react';
import Link from '@docusaurus/Link';
import { useAuth } from '../../context/AuthContext';
import styles from './AccessDenied.module.css';

const AccessDenied = () => {
  const { roleDisplayName, isAuthenticated } = useAuth();

  return (
    <main className={styles.container}>
      <p className={styles.eyebrow}>Restricted page</p>
      <h1 className={styles.title}>Technical documentation is protected</h1>

      {isAuthenticated ? (
        <p className={styles.message}>
          Your current role is <strong>{roleDisplayName}</strong>. This page requires admin, campus admin,
          school IT, or an authorized technical-doc email.
        </p>
      ) : (
        <p className={styles.message}>Sign in with an account that has technical documentation access.</p>
      )}

      <div className={styles.actions}>
        <Link to="/" className="button button--primary">
          Go to docs home
        </Link>
        <Link to="/user/getting-started" className="button button--secondary">
          Open user guide
        </Link>
      </div>
    </main>
  );
};

export default AccessDenied;
