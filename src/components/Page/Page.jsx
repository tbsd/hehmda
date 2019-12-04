import React from 'react';
import classes from './Page.module.css';
import Dialogs from './Dialogs/Dialogs';
import Content from './Content/Content';

const Page = () => {
    return (
        <div>
            <Dialogs/>
            <Content/>
        </div>
    );
}

export default Page;