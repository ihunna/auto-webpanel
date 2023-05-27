const showHide = (action='show',e=Array,text=String,styles=Array) =>{
    if (action === 'show'){
        e.forEach(el => {
          if (el.classList.contains('alert')){
            el.innerHTML = text;
            el.style.background = styles.bg;
            el.style.color = styles.color;
            el.classList.remove('no-show')
            el.classList.add(action);
          }else{
            el.classList.remove('no-show')
            el.classList.add(action);
          }

      });
    }

    else if (action === 'show-menu'){
        e.forEach(el => {
            el.classList.remove('no-show');
            el.classList.add(action);
        });
    }

    else if (action === 'no-show'){
        e.forEach(el => {
            el.classList.remove('show');
            el.classList.remove('show-menu');
            el.classList.add(action);
        });
    }
}

const createModal = (element=Element,type=String,items=Array,text=String,cat=String) => {
    element.innerHTML = ``;
    const m = doc.createElement('div'); 
    m.classList.remove('for-m-item-display');
    m.classList.add('modal', 'for-s-item-display');
    
    const closeBtn = doc.createElement('span');
    closeBtn.classList.add('close');
    const closeIcon = doc.createElement('i');
    closeIcon.classList.add('fa', 'fa-close');
    closeBtn.appendChild(closeIcon);
    
    m.appendChild(closeBtn);

    if (type === 'prompt'){
        m.style.height = '140px'
        const yesAction = doc.createElement('div');
        yesAction.classList.add('yes-action');

        const yesText = doc.createElement('p');
        yesText.textContent = text;
        yesAction.appendChild(yesText);

        const yesLink = doc.createElement('a');
        yesLink.href = '#';
        yesLink.classList.add('eleveted-a');
        yesLink.textContent = 'Yes';
        yesAction.appendChild(yesLink); 
        m.appendChild(yesAction);

        yesLink.addEventListener('click',(e)=>{
          e.preventDefault();

          text = `Deleting ${cat}`;
          showHide('no-show',[overlay,modal]);
          showHide('show',[alertBox],text,{'bg':colorSuccess,'color':colorLessWhite});

          sendRequest('POST',`/delete/${cat}`,{'data':items})
          .then(response => {
            showHide('no-show',[alertBox]);
            con.log(response)
            showHide('show',[alertBox],`${cat} deleting successful`,{'bg':colorSuccess,'color':colorLessWhite});
            setTimeout(() => {
              showHide('no-show',[alertBox])
              window.location.reload();
            },
            5000);
          })
          .catch(error => {
            showHide('no-show',[alertBox]);
            showHide('show',[alertBox],`${cat} deleting unsuccessful`,{'bg':colorDanger,'color':colorLessWhite});
            setTimeout(() => showHide('no-show',[alertBox]), 5000);
            con.error(error);
          });
        })
    }
    else if (type === 'mModal'){
        m.classList.remove('for-s-item-display');
        m.classList.add('for-m-item-display');

        const ul = doc.createElement('ul');
        ul.classList.add('m-item-display', 'scroll');

        for (let i = 0; i < 8; i++){
            const li = doc.createElement('li');

            const itemHeaderDiv = doc.createElement('div');
            itemHeaderDiv.classList.add('item-header');
            itemHeaderDiv.style.background = "url('../../images/low-angle-businessman.jpg')";
            itemHeaderDiv.style.backgroundRepeat = 'no-repeat';
            itemHeaderDiv.style.backgroundSize = 'cover';
            itemHeaderDiv.style.backgroundPosition = 'center';

            const itemHeaderOverlayDiv = doc.createElement('div');
            itemHeaderOverlayDiv.classList.add('item-header-overlay');
            itemHeaderDiv.appendChild(itemHeaderOverlayDiv);

            const likeHeartDiv = doc.createElement('div');
            likeHeartDiv.classList.add('like-heart');
            const likeIconElement = doc.createElement('i');
            likeIconElement.classList.add('fas', 'fa-heart', 'liked');
            likeHeartDiv.appendChild(likeIconElement);
            itemHeaderDiv.appendChild(likeHeartDiv);

            const itemHdDiv = doc.createElement('div'); 
            itemHdDiv.classList.add('item-hd');

            const itemNameAgeDiv = doc.createElement('div');
            itemNameAgeDiv.classList.add('item-name-age');
            const itemNameElement = doc.createElement('h3');
            itemNameElement.classList.add('item-name');
            itemNameElement.textContent = 'Kevin Debrun';
            const vIconSpan = doc.createElement('span');
            vIconSpan.classList.add('v-icon');
            const vIconElement = doc.createElement('i');
            vIconElement.classList.add('fas', 'fa-check-circle');
            vIconSpan.appendChild(vIconElement);
            itemNameElement.appendChild(vIconSpan);
            itemNameAgeDiv.appendChild(itemNameElement);
            const itemAgeElement = doc.createElement('h3');
            itemAgeElement.classList.add('item-age');
            itemAgeElement.textContent = '23';
            itemNameAgeDiv.appendChild(itemAgeElement);
            itemHdDiv.appendChild(itemNameAgeDiv);

            const itemLocationDiv = doc.createElement('div');
            itemLocationDiv.classList.add('item-location');
            const locationIconElement = doc.createElement('i');
            locationIconElement.classList.add('fa', 'fa-map-marker');
            itemLocationDiv.appendChild(locationIconElement);
            itemLocationDiv.textContent = 'New York, United States';
            itemHdDiv.appendChild(itemLocationDiv);

            const itemStatsDiv = doc.createElement('div');
            itemStatsDiv.classList.add('item-stats');
            const likedMeDiv = doc.createElement('div');
            likedMeDiv.classList.add('eleveted-a');
            likedMeDiv.textContent = 'liked me';
            const matchedDiv = doc.createElement('div');
            matchedDiv.classList.add('eleveted-a');
            matchedDiv.textContent = 'matched';
            itemStatsDiv.appendChild(likedMeDiv);
            itemStatsDiv.appendChild(matchedDiv);
            itemHdDiv.appendChild(itemStatsDiv);

            itemHeaderDiv.appendChild(itemHdDiv);
            li.appendChild(itemHeaderDiv);

            const itemBioDiv = doc.createElement('div');
            itemBioDiv.classList.add('item-bio', 'scroll');
            const bioParagraph = doc.createElement('p');
            bioParagraph.textContent = 'From Florida, just moved to DC!';
            itemBioDiv.appendChild(bioParagraph);
            li.appendChild(itemBioDiv);

            ul.appendChild(li);
        }
        
        m.appendChild(ul);
    }

    else if (type === 'sModalImg-upload' || type === 'sModalImg') {
        let text;
        m.classList.remove('for-m-item-display');
        m.classList.add('modal', 'for-s-item-display');
        const imgDiv = doc.createElement('div'); 
        imgDiv.classList.add('s-item-display', 'scroll');
        
        items.forEach(e =>{
            con.log(e)
            const imgHolder = doc.createElement('div');
            imgHolder.classList.add('img-holder');

            const image = doc.createElement('img');
            image.src = `${e.url}`;
            image.alt = '';

            const imgName = doc.createElement('div');
            imgName.classList.add('img-name');
            imgName.textContent =  `${e.name}`;

            imgHolder.appendChild(image); 
            imgHolder.appendChild(imgName);

            imgDiv.appendChild(imgHolder); 
            m.appendChild(imgDiv);
        });
        const actionsElement = doc.createElement('div');
            actionsElement.classList.add('s-item-actions');

            const actionLink = doc.createElement('a');
            actionLink.href = '';
            actionLink.classList.add('eleveted-a');

            if (type === 'sModalImg'){
              actionLink.textContent = 'delete';
              actionLink.classList.remove('upload');
              actionLink.classList.add('delete');
              text = 'Do you want to delete this image?';

              actionLink.addEventListener('click',(e) => {
                e.preventDefault();
                createModal(modal,'prompt',items,text,cat)
                showHide('show',[overlay,modal]);
              });

            }else{
              actionLink.textContent = 'upload';
              actionLink.classList.remove('delete');
              actionLink.classList.add('upload');

               actionLink.addEventListener('click',(e) => {
                e.preventDefault();
                if (items.length < 1){
                  text = 'No image to upload!';
                  showHide('show',[alertBox],text,{'bg':colorSec,'color':colorLessDark});
                }else{
                  text = 'Image(s) uploading ...';
                  showHide('no-show',[overlay,modal]);
                  showHide('show',[alertBox],text,{'bg':colorSuccess,'color':colorLessWhite});
                  const url = window.location.href;
                  const urlParts = url.split("/");

                  const profileIndex = 4;
                  const myprofile = urlParts[profileIndex];

                  sendRequest('POST',`/upload-images/${myprofile}`,{'data':items})
                  .then(response => {
                    showHide('no-show',[alertBox]);
                    con.log(response)
                    showHide('show',[alertBox],'image upload successful',{'bg':colorSuccess,'color':colorLessWhite});
                    setTimeout(() => {
                      showHide('no-show',[alertBox])
                      window.location.replace('/images/'+myprofile)
                    },
                    7000);
                  })
                  .catch(error => {
                    showHide('no-show',[alertBox]);
                    showHide('show',[alertBox],'image upload unsuccessful',{'bg':colorDanger,'color':colorLessWhite});
                    setTimeout(() => showHide('no-show',[alertBox]), 5000);
                    con.error(error);
                  });
                }
              });
              
            }

            actionsElement.appendChild(actionLink);
            m.appendChild(actionsElement);
    }

    else if (type === 'uploadImages'){
        const inputFileDiv = document.createElement('div');
        inputFileDiv.classList.add('file-upload');

        const fileInput = document.createElement('input');
        fileInput.setAttribute('type', 'file');
        fileInput.setAttribute('id', 'file-input');
        fileInput.setAttribute('name', 'file-input');
        fileInput.setAttribute('accept','.jpg, .jpeg, .gif, .png');
        fileInput.setAttribute('multiple','');

        const fileLabel = document.createElement('label');
        fileLabel.setAttribute('for', 'file-input');
        fileLabel.classList.add('input-label');

        const fileIcon = document.createElement('i');
        fileIcon.classList.add('far', 'fa-folder-open');

        const labelText = document.createTextNode('Choose a file');

        fileLabel.appendChild(fileIcon); 
        fileLabel.appendChild(labelText); 

        inputFileDiv.appendChild(fileInput); 
        inputFileDiv.appendChild(fileLabel);

        m.appendChild(inputFileDiv);

        fileInput.addEventListener('change', (e) => {
            getFiles(fileInput)
              .then((files) => {
                createModal(modal, 'sModalImg-upload', files);
                showHide('show', [overlay, modal]);
              })
              .catch((error) => {
                const text = error
                showHide('show',[alertBox],text,{'bg':colorDanger,'color':colorLessWhite});
                setTimeout(() => showHide('no-show',[alertBox]), 5000)
                console.error(error);
              });
          });
    }
    element.appendChild(m);
    closeBtn.addEventListener('click',() => showHide('no-show',[overlay,modal]));
}

const getFiles = (fileInput = Element) => {
    return new Promise((resolve, reject) => {
      const selectedFiles = fileInput.files;
      if (selectedFiles.length > 0) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/gif', 'image/png'];
        let files = [];
  
        let completedCount = 0; // Counter for completed file reads
  
        const checkCompletion = () => {
          if (completedCount === selectedFiles.length) {
            resolve(files);
          }
        };
  
        for (let i = 0; i < selectedFiles.length; i++) {
          if (allowedTypes.includes(selectedFiles[i].type)) {
            const reader = new FileReader();
            reader.addEventListener('load', (e) => {
              files.push({ 'url': e.target.result, 'name': selectedFiles[i].name });
              completedCount++; 
              checkCompletion();
            });

            reader.readAsDataURL(selectedFiles[i]);
          } else {
            const labelText = document.createTextNode('File not supported');
            const label = doc.querySelector('.input-label');
            label.childNodes.forEach(node => {
                if (node.nodeType === Node.TEXT_NODE) {
                node.textContent = '';
                }
            });
            label.appendChild(labelText);
            reject(new Error('Wrong file type (choose image/jpeg, image/jpg, image/gif, image/png)'));
            return;
          }
        }
      } else {
        reject(new Error('No files selected'));
      }
    });
  };



const sendRequest = (method, url, data = null, formData = null) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open(method, url);
  
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const response = JSON.parse(xhr.responseText);
          const msg = response.msg;
          resolve(msg);
        } else {
          const response = JSON.parse(xhr.responseText);
          const error = response.msg;
          reject(new Error(error));
        }
      };
  
      xhr.onerror = () => {
        reject(new Error('Network error'));
      };
  
      if (method === 'POST' || method === 'PUT') {
        if (formData) {
          xhr.send(formData);
        } else {
          xhr.setRequestHeader('Content-Type', 'application/json');
          xhr.send(JSON.stringify(data));
        }
      } else {
        xhr.send();
      }
    });
  }
  
  

export {showHide,createModal,sendRequest}