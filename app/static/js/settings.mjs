'use strict';
import { showHide, createModal, sendRequest} from "./utils.mjs";

(() =>{
    try{
        menuBtn.addEventListener('click',() => showHide('show-menu',[overlay,uCard,sideBar,closeMenuBtn]));
        closeMenuBtn.addEventListener('click',() => showHide('no-show',[overlay,uCard,sideBar,closeMenuBtn]));
    }catch(error){con.log(error)}
    try{
        const table = doc.querySelector('table');
        const td = table.querySelectorAll('td.actions');
        td.forEach(e =>{
            const aSpan = e.querySelector('.action-btns');
            const actionBtn = aSpan.querySelectorAll('a');
            actionBtn.forEach(a=>{
                if (a.classList.contains('block-this-account?') || 
                    a.classList.contains('unblock-this-account?') ||
                    a.classList.contains('make-super?'))

                a.addEventListener('click',(event) =>{
                    event.preventDefault();
                    const text = a.classList[a.classList.length - 1].replace(/-/g, ' ');
                    let action;
                    if (a.classList.contains('block-this-account?')){action = 'block'}
                    else if (a.classList.contains('unblock-this-account?')){action='unblock'}
                    else if (a.classList.contains('make-super?')){action='make-super'}
                    createModal(modal,'prompt',[{'admin_id':e.id}],text,'admin',action)
                    showHide('show',[overlay,modal]);
                })
            })



            const toolKit = e.querySelector('i');
            toolKit.addEventListener('click',()=>{
                td.forEach(a =>{
                    const aSpan = a.querySelector('.action-btns');
                    showHide('no-show',[aSpan]);
                })
                const aSpan = e.querySelector('.action-btns');
                if(aSpan.classList.contains('shown')){
                    aSpan.classList.remove('shown');
                    showHide('no-show',[aSpan]);
                }else{
                    showHide('show',[aSpan]);
                    aSpan.classList.add('shown');
                }
            })
        })

    }catch(error){con.log(error)}
    try{
        const dBtn = doc.querySelectorAll('.delete');
        dBtn.forEach(e => {
            e.addEventListener('click',(event) => {
                event.preventDefault();
                const text = e.classList[e.classList.length - 1].replace(/-/g, ' ');
                if (e.classList.contains('Click-on-an-account-to-delete'.toLowerCase())
                || e.classList.contains('Click-on-an-image-to-delete'.toLowerCase())){
                    showHide('show',[alertBox],text,{'bg':colorSec,'color':colorLessDark});
                    setTimeout(() => showHide('no-show',[alertBox]),5000)
                }else{
                    createModal(modal,'prompt',[],text)
                    showHide('show',[overlay,modal]);
                }
            });
        });
    }catch (error){con.log(error)}
    closeBtn.forEach(e =>{
        e.addEventListener('click',() => showHide('no-show',[overlay,modal]));
    });
    try{
        const viewMatches = doc.querySelectorAll('.view-matches');
        viewMatches.forEach(e=>{
            e.addEventListener('click',(e) =>{
                e.preventDefault();
                const matches = JSON.parse(_matches.replace('"{','{').replace('}"','}')).data;
                con.log(matches)
                createModal(modal,'mModal',matches);
                showHide('show',[overlay,modal]);
            });
        });
    }catch (error){con.log(error)}
    try{
        const viewAll = doc.querySelector('.view-all');
        viewAll.addEventListener('click',(e) => {
            e.preventDefault();
            createModal(modal,'sModalImg',[]);
            showHide('show',[overlay,modal]);
        });
    }catch(error){con.log(error)}
    try{
        const uploadImages = doc.querySelectorAll('.upload-image');
        uploadImages.forEach(e => {
            e.addEventListener('click',(e) => {
                e.preventDefault();
                createModal(modal,'uploadImages')
                showHide('show',[overlay,modal]);
            });
        });
    }catch (error){con.log(error)}
    try{
        const accOpForm = doc.querySelector('#account-op-form');
        accOpForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(accOpForm);
    
            sendRequest('POST', '/create-accounts', null, formData)
            .then(response => {
                showHide('show',[alertBox],response,{'bg':colorSuccess,'color':colorLessWhite});
                accOpForm.reset();
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const swipeOpForm = doc.querySelector('#swipe-op-form');
        swipeOpForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(swipeOpForm);
    
            sendRequest('POST', '/swipe', null, formData)
            .then(response => {
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                swipeOpForm.reset();
                setTimeout(() => showHide('no-show',[alertBox]), 5000);
                setTimeout(() => location.reload(), 5000)
            })
            .catch(error => {
                showHide('show',[alertBox],response.msg,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const platformForm = doc.querySelector('#platform-form');
        platformForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(platformForm);
            
            sendRequest('POST', '/add-platform', null, formData)
            .then(response => {
                showHide('show',[alertBox],response,{'bg':colorSuccess,'color':colorLessWhite});
                platformForm.reset();
                setTimeout(() => {
                    showHide('no-show',[alertBox]);
                    window.location.href = '/dashboard'
                }, 5000)
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const modelForm = doc.querySelector('#model-form');
        modelForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(modelForm);
            
            const url = modelForm.classList.contains('edit-model')? '/models/edit-model':'models/add-model'
            sendRequest('POST', url, null, formData).then(response => {
                modelForm.reset()
                showHide('show',[alertBox],response,{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => {
                    showHide('no-show',[alertBox]);
                    window.location.href='/models'
                }, 5000)
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const adminForm = doc.querySelector('#admin-form');
        adminForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(adminForm);
            
            sendRequest('POST', '/admins/edit-admin', null, formData).then(response => {
                adminForm.reset()
                showHide('show',[alertBox],response,{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => {
                    showHide('no-show',[alertBox]);
                    window.location.href='/admins'
                }, 5000)
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const accountForm = doc.querySelector('#account-form');
        accountForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(accountForm);
            
            const url = '/account-page/edit-account'
            sendRequest('POST', url, null, formData).then(response => {
                showHide('show',[alertBox],response,{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const signupForm = doc.querySelector('#signup-form');
        signupForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(signupForm);
            
            sendRequest('POST', '/signup', null, formData).then(response => {
                const errors = doc.querySelector('.errors');
                errors.innerHTML = '';
                signupForm.reset();
                con.log(response)
                showHide('show',[alertBox],'Signup successful',{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000);
            })
            .catch(error => {
                const errors = doc.querySelector('.errors');
                errors.innerHTML = `${error}`;
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000);
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const loginForm = doc.querySelector('#login-form');
        loginForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(loginForm);
            
            sendRequest('POST', '/login', null, formData).then(response => {
                const errors = doc.querySelector('.errors');
                errors.innerHTML = '';
                loginForm.reset();
                con.log(response)
                showHide('show',[alertBox],'Login successful',{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => {
                    showHide('no-show',[alertBox]);
                    window.location.replace('/dashboard')
            }, 5000);
            })
            .catch(error => {
                const errors = doc.querySelector('.errors');
                errors.innerHTML = `${error}`;
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000);
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const images = doc.querySelector('#images');
        const imageLi = images.querySelectorAll('li');
        imageLi.forEach(li => {
            li.addEventListener('click',()=>{
                const imgSrc = li.querySelector('img').getAttribute('src');
                const imgName = imgSrc.split('/dashboard');
                const url = imgSrc;
                const urlParts = url.split("/");

                const profileIndex = 5;
                const myprofile = urlParts[profileIndex];
                createModal(modal,'sModalImg',[
                    {'url':imgSrc,
                    'name':imgName[imgName.length - 1],
                    'type':myprofile,
                    }],'','image');
                showHide('show',[overlay,modal]);
            })
        })
    }catch(error){con.log(error)}
})()

