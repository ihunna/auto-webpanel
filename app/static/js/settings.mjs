'use strict';
import { showHide, createModal, sendRequest} from "./utils.mjs";

(() =>{
    closeBtn.forEach(e =>{
        e.addEventListener('click',() => {
            const action = e.getAttribute('data-action');
            let target = action =='close-modal'?[overlay,modal]:[e.parentNode];
            showHide('no-show',target);
        })
    });
    try{
        const toggleMap = doc.querySelector('#toggle-map');
        const map = doc.querySelector('#op-map');
        toggleMap.addEventListener('click',(e)=>{
            e.preventDefault();
            e.target.innerHTML = ``;
            if (map.classList.contains('show')){
                showHide('no-show',[map]);
                e.target.innerHTML = `open map &nbsp;
                <i class="fas fa-map-marked"></i>`;
            }
            else{
                showHide('show',[map]);
                e.target.innerHTML = `close map &nbsp;
                <i class="fas fa-map-marked"></i>`;
            }
            console.log(map)
        })
    }catch(error){con.log(error)}
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
            const toolKit = e.querySelector('i');
            toolKit.addEventListener('click',()=>{
                td.forEach(a =>{
                    const aSpan = a.querySelector('.action-btns');
                    showHide('no-show',[aSpan]);
                })
                const aSpan = e.querySelector('.action-btns');
                if(aSpan.classList.contains('shown') || aSpan.classList.contains('disabled')){
                    aSpan.classList.remove('shown');
                    showHide('no-show',[aSpan]);
                }else{
                    showHide('show',[aSpan]);
                    aSpan.classList.add('shown');
                }
            })
        })

        const checkBtn = table.querySelector('th.check-all #check-all')
        const checkBoxes = table.querySelectorAll('td .check-input');
        checkBtn.addEventListener('click',()=>{
            for (const checkbox of checkBoxes) {
                checkbox.checked = checkBtn.checked;
            }
            showDeleteBtn(checkBoxes);
        });
        checkBoxes.forEach(e =>{
           e.addEventListener('change',()=>{ 
            showDeleteBtn([e]);
            })
        })

        const showDeleteBtn = (elements,data='') =>{
            const deleteAll = doc.getElementById('delete-all');
            let checked = 0;
            elements.forEach(e=>{
                if (e.checked){
                    data += e.value + '\n';
                    deleteAll.setAttribute('data-action-data',data.trim());
                    checked++
                }
            });
            if (checked > 0){
                deleteAll.parentNode.classList.add('add-more');
                deleteAll.classList.remove('no-show');
            }else{
                deleteAll.parentNode.classList.remove('add-more');
                deleteAll.classList.add('no-show');
            }
        }

        const clickables = table.querySelectorAll('tbody tr td.clickable');
        clickables.forEach(e =>{
            e.addEventListener('click',()=>{
                const category = e.parentNode.getAttribute('data-category');
                if(category != 'admins'){
                    const url = e.parentNode.getAttribute('data-url');
                    window.location.href = url;
                }
            })
        })

    }catch(error){con.log(error)}
    try{
        const logoutBtn = doc.querySelectorAll('.logout-btn')
        logoutBtn.forEach(a => {
            a.addEventListener('click',(e) => {
                e.preventDefault();
                createModal(modal,'prompt',[],'Do you really want to logout?','logout','','logout')
                showHide('show',[overlay,modal]);
            })
        })
    }catch(error){con.log(error)}
    try{
        const dBtn = doc.querySelectorAll('.action');
        dBtn.forEach(e => {
            e.addEventListener('click',(event) => {
                event.preventDefault();
                const actionText = e.getAttribute('data-action-message');
                const text = e.getAttribute('data-action-prompt');
                const action = e.getAttribute('data-action');
                const route = e.getAttribute('data-url');
                const cat = e.getAttribute('data-action-category');
                let data = cat=='do-multiple'?[
                    {'data':e.getAttribute('data-action-data').split('\n')}
                    ]:[{'id':e.getAttribute('data-action-id')}]

                if (action !== 'update-account'){
                    con.log(data)
                    createModal(modal,'prompt',data,text,action,route,actionText)
                    showHide('show',[overlay,modal]);
                }else{
                    // showHide('no-show',[e.parentNode]);
                    showHide('show',[alertBox],actionText,{'bg':colorSuccess,'color':colorLessWhite});
                    sendRequest('POST',route,{'data':data})
                    .then(response => {
                        showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                        setTimeout(() => showHide('no-show',[alertBox]), 3000)
                    })
                    .then(()=>{
                        window.location.reload();
                    })
                    .catch(error => {
                        showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                        setTimeout(() => showHide('no-show',[alertBox]), 5000)
                        con.error(error);
                    });
                }
            });
        });
    }catch (error){con.log(error)}
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
            const imageList = profileImages;
            const images = Array.from(imageList).map((img) => {
                const url = img;
                let name = url.split('/')
                name = name[name.length-1]
                return {
                  url: url,
                  name: name,
                  'id':null,
                };
              });
            createModal(modal,'sModalImg',images,null,'profile-images');
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
    try {
        const image_type = doc.querySelector('#image-type');
        const getGdriveImages = () => {
          const gdriveBtn = document.getElementById('gdrive-btn');
          const gdriveBtnUpload = document.getElementById('gdrive-btn-upload');
          const driveKey = document.getElementById('drive_key').value;
          const gdriveLink = document.getElementById('gdrive-link').value;
          const gdriveInfo = document.getElementById('gdrive-display');
      
          if (gdriveLink === '') {
            console.log('empty link value');
            document.querySelector('.errors').innerHTML = `Drive link cannot be empty!`;
          } else {
            const urlParts = gdriveLink.split('/');
            const folderId = urlParts[urlParts.length - 1];
            const apiUrl = `https://www.googleapis.com/drive/v3/files?q='${encodeURIComponent(folderId)}'+in+parents&key=${driveKey}`;
            // showHide('show', [alertBox], 'getting images', { 'bg': colorSuccess, 'color': colorLessWhite });
            showHide('show',[alertBox],'Fetching images...',{'bg':colorSuccess,'color':colorLessWhite});
            fetch(apiUrl)
              .then(response => {
                if (!response.ok) {
                  throw response.json();
                }
                return response.json();
              })
              .then(response => {
                const imageLinks = response.files.map(file => `https://drive.google.com/uc?export=download&id=${file.id}`);
                doc.querySelector('#data').value = imageLinks;
                showHide('show', [gdriveInfo], `${imageLinks.length} images to upload`);
                showHide('show', [gdriveBtnUpload]);
                // gdriveBtn.id = '';
                // gdriveBtn.type = 'submit';
                // gdriveBtn.value = 'Upload';
                console.log(imageLinks);
                // showHide('show', [alertBox], 'Operation successful', { 'bg': colorSuccess, 'color': colorLessWhite });
                // const removeListenerPromise = new Promise((resolve) => {
                //   setTimeout(() => {
                //     gdriveBtn.removeEventListener('click', getGdriveImages);
                //     resolve();
                //   }, 0);
                // });
      
                // return removeListenerPromise;
              })
              .catch(error => {
                if (error instanceof Promise) {
                  error.then(errorMessage => {
                    document.querySelector('.errors').innerHTML = `${errorMessage.error.status}`;
                    showHide('show', [alertBox], errorMessage.error.status, { 'bg': colorDanger, 'color': colorLessWhite });
                    console.error('Error:', errorMessage.error.message);
                  });
                } else {
                  console.error('Error:', error);
                }
              })
              .then(() => {
                setTimeout(() => showHide('no-show', [alertBox]), 5000);
              });
          }
        };
      
        const gdriveBtn = document.getElementById('gdrive-btn');
        gdriveBtn.addEventListener('click', getGdriveImages);
      } catch (error) {con.log(error);}      
    try{
        const gDriveForm = doc.querySelector('#gdrive-form');
        gDriveForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(gDriveForm);
            const image_type = gDriveForm.querySelector('#image-type')
            showHide('show',[alertBox],'Image(s) uploading...',{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', `/upload-images/${image_type.value}/gdrive`, null, formData)
            .then(response => {
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                gDriveForm.reset();
                setTimeout(() => {
                    showHide('no-show', [alertBox]);
                    window.location.href = `/images/${image_type.value}`;
                }, 5000);
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                con.error(error)
                setTimeout(() => showHide('no-show',[alertBox]), 5000);
            })
        })
    }catch(error){con.log(error)}
    try{
        const accOpForm = doc.querySelector('#account-op-form');
        accOpForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(accOpForm);
            const url = accOpForm.getAttribute('data-action-url');
            const text = accOpForm.getAttribute('data-action-message');
            showHide('show',[alertBox],text,{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', url, null, formData)
            .then(response => {
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                accOpForm.reset();
                setTimeout(() => showHide('no-show',[alertBox]), 3000)
            })
            .then(()=>{
                window.location.href = '/create-accounts'
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

            showHide('show',[alertBox],'Starting swipe operation...',{'bg':colorSuccess,'color':colorLessWhite});
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
            showHide('show',[alertBox],'Adding platform...',{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', '/add-platform', null, formData)
            .then(response => {
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
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
            const action = modelForm.getAttribute('data-action');

            const url = `/models/${action}`;
            let text = modelForm.getAttribute('data-action-message');
            showHide('show',[alertBox],text,{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', url, null, formData).then(response => {
                modelForm.reset()
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
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
        const opModels = doc.querySelectorAll('.op-model')
        opModels.forEach(opModel =>{
            opModel.addEventListener('input',(e)=>{
                showHide('show',[alertBox],'Setting model...',{'bg':colorSuccess,'color':colorLessWhite});
                sendRequest('POST','/models/set-model', {'data':e.target.value}).then(response => {
                    showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});

                    const opSwipe = doc.querySelector('#op-swipe-group');
                    opSwipe.innerHTML=``;
                    const swipeGroups = response.model_swipe_schedules;
                    const optionElement = document.createElement('option');
                        optionElement.value = '';
                        optionElement.setAttribute('disabled','')
                        optionElement.textContent = 'select schedule group';
                        opSwipe.appendChild(optionElement);
                    swipeGroups.forEach(swipe=>{
                        const optionElement = document.createElement('option');
                        optionElement.value = swipe.id;
                        optionElement.textContent = swipe.name;
                        opSwipe.appendChild(optionElement);
                    })
                    doc.querySelector('.model-tag').textContent = `${response.model.full_name}`;
                    doc.querySelector('#current-model').textContent = `(${response.model.full_name})`;
                })
                .then(() =>{
                    setTimeout(() => {
                        showHide('no-show',[alertBox]);
                    }, 3000)
                })
                .catch(error => {
                    showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                    setTimeout(() => showHide('no-show',[alertBox]), 5000)
                    con.error(error);
                });
            })
        })
    }catch(error){con.log(error)}
    try{
        const scheduleForm = doc.querySelector('#schedule-form');
        scheduleForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(scheduleForm);

            const action = scheduleForm.getAttribute('data-action');
            const actionMsg = scheduleForm.getAttribute('data-action-message');
            const url = `/schedules/${action}`;

            if (action == 'finish-schedule'){showHide('show',[alertBox],actionMsg,{'bg':colorSuccess,'color':colorLessWhite});}
            sendRequest('POST', url, null, formData).then(response => {
                scheduleForm.reset()
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                if (response.action && response.action === 'finish-schedule'){
                    window.location.href=`/schedules?action=next&s=${response.schedule}&type=${response.action_type}&next=${response.next}&interval=${response.date_interval}&swipe_percent=${response.swipe_percent}`
                }else{
                setTimeout(() => {
                    let next = response.next != null? `${response.next}`:`/schedules`
                    showHide('no-show',[alertBox],response.msg);
                    window.location.href=next;
                }, 3000)
            }
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
            
            sendRequest('POST',`/admins/${action}`, null, formData).then(response => {
                adminForm.reset()
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
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
            const action = accountForm.getAttribute('data-action');
            const actionMsg = accountForm.getAttribute('data-action-message');
            const url = `/account-page/${action}`;
            showHide('show',[alertBox],actionMsg,{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', url, null, formData).then(response => {
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
            })
            .then(()=>{
                const accountId = accountForm.querySelector('#account-id').value;
                window.location.href = `/account-page?account=${accountId}&action=view-details#preferences`
            })
            .catch(error => {
                showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                con.error(error);
            });
        })
    }catch(error){con.log(error)}
    try{
        const updateLocation = doc.querySelector('#updateButton');
        updateLocation.addEventListener('click',(e)=>{
            e.preventDefault();
            let location = doc.querySelector('#op-location');
            const accountId = location.getAttribute('data-account-id');

            location = String(location.value).split(',')
            if (location.length > 1){

                const lat = parseFloat(location[0]);
                const long = parseFloat(location[1]);
    
                const data = {'account_id':accountId,'data':{'long':long,'lat':lat}}
                showHide('show',[alertBox],'updating location...',{'bg':colorSuccess,'color':colorLessWhite});
                sendRequest('POST', `/account-page/map`,data,null).then(response => {
                    showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                    setTimeout(() => {
                        showHide('no-show',[alertBox]);
                    },
                    3000);
                })
                .catch(error => {
                    showHide('show',[alertBox],error,{'bg':colorDanger,'color':colorLessWhite});
                    setTimeout(() => showHide('no-show',[alertBox]), 5000);
                    con.error(error);
                });
            }
        })
    }catch(error){con.log(error)}
    try{
        const signupForm = doc.querySelector('#signup-form');
        signupForm.addEventListener('submit',(e)=>{
            e.preventDefault();
            const formData = new FormData(signupForm);
            
            showHide('show',[alertBox],'Signing up user...',{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', `${signup_url}`, null, formData).then(response => {
                const errors = doc.querySelector('.errors');
                errors.innerHTML = '';
                signupForm.reset();
                con.log(response)
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
                setTimeout(() => {
                    showHide('no-show',[alertBox]), 
                    window.location.href = '/admins';},
                5000);
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
            
            showHide('show',[alertBox],'Logging you in...',{'bg':colorSuccess,'color':colorLessWhite});
            sendRequest('POST', '/login', null, formData).then(response => {
                const errors = doc.querySelector('.errors');
                errors.innerHTML = '';
                loginForm.reset();
                con.log(response)
                showHide('show',[alertBox],response.msg,{'bg':colorSuccess,'color':colorLessWhite});
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
                const imgName = imgSrc.split('/');
                const imageId = li.querySelector('img').id;

                const type = li.getAttribute('data-image-type');
                const cat = li.getAttribute('data-image-category')

                const actionText = li.getAttribute('data-action-message');
                const text = li.getAttribute('data-action-prompt');
                const action = li.getAttribute('data-action');
                const route = li.getAttribute('data-url');

                createModal(modal,'sModalImg',[
                    {'url':imgSrc,
                    'name':imgName[imgName.length - 1],
                    'type':type,
                    'id':imageId,
                    'upload_type':cat
                    }],text,action,route,actionText);
                showHide('show',[overlay,modal]);
            })
        })
    }catch(error){con.log(error)}
})()

