import React from 'react';
import logo from './logo.svg';
import './App.css';
import Header from './components/Header/Header';
import Content from './components/Content/Content';
import Dialogs from './components/Dialogs/Dialogs';

const App = () => {
    return (
	<div className='app-wrapper'>
          <Header />
          <Content />
          <Dialogs />
        </div>
    );
}

export default App;