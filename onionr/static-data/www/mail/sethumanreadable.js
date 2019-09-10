function loadHumanReadableToCache(key){
    fetch('/getHumanReadable/' + key, {
        headers: {
          "token": webpass
        }})
    .then((resp) => resp.text())
    .then(function(resp) {
        humanReadableCache[key] = resp
    })
}

function setHumanReadableValue(el, key){
    if (typeof humanReadableCache[key] != 'undefined'){
        el.value = humanReadableCache[key]
        return
    }
    else{
        loadHumanReadableToCache(key)
        setTimeout(function(){setHumanReadableValue(el, key)}, 100)
        return
    }
}