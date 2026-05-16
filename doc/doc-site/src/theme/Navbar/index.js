import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import Navbar from '@theme-original/Navbar';
import LoginButton from '../../components/Auth/LoginButton';
import { useAuth } from '../../context/AuthContext';

export default function NavbarWrapper(props) {
  const { user } = useAuth();
  const [navbarRight, setNavbarRight] = useState(null);

  useEffect(() => {
    setNavbarRight(document.querySelector('.navbar__items--right'));
  }, []);

  return (
    <>
      <Navbar {...props} />
      {user && navbarRight ? createPortal(<LoginButton />, navbarRight) : null}
    </>
  );
}
