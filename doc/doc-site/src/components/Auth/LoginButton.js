import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { getAccessLabel } from '../../config/roles';
import styles from './LoginButton.module.css';

const LoginButton = () => {
  const { user, role, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) return null;

  return (
    <div className={styles.userInfo} aria-label="Documentation account">
      <span className={styles.roleBadge}>{getAccessLabel(role)}</span>
      <span className={styles.userName} title={user.email || user.username}>
        {user.email || user.username}
      </span>
      <button type="button" onClick={logout} className={styles.logoutButton}>
        Sign out
      </button>
    </div>
  );
};

export default LoginButton;
