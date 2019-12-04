import React from 'react';
import logo from './logo.svg';
import './App.css';
import Header from './components/Header/Header';
import Page from './components/Page/Page';
import SignupPg from './components/SignupPg/SignupPg';
import SigninPg from './components/SigninPg/SigninPg';

const App = () => {
    return (
	<div className='app-wrapper'>
          <Header />
          <SignupPg />
          <SigninPg />
          <Page />
        </div>
    );
}

export default App;