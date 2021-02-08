/*
    Onionr - Private P2P Communication

    This file loads stats to show on the main node web page

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
*/
uptimeDisplay = document.getElementById('uptime')
connectedDisplay = document.getElementById('connectedNodes')
storedBlockDisplay = document.getElementById('storedBlocks')
queuedBlockDisplay = document.getElementById('blockQueue')
lastIncoming = document.getElementById('lastIncoming')
totalRec = document.getElementById('totalRec')
securityLevel = document.getElementById('securityLevel')
sec_description_str = 'unknown'

statsInterval = null

function showSecStatNotice(){
    var secWarnEls = document.getElementsByClassName('secRequestNotice')
    for (el = 0; el < secWarnEls.length; el++){
        secWarnEls[el].style.display = 'block'
    }
}

function seconds2time (seconds) {
    //func from https://stackoverflow.com/a/7579799/2465421 by https://stackoverflow.com/users/14555/jottos
    var hours   = Math.floor(seconds / 3600)
    var minutes = Math.floor((seconds - (hours * 3600)) / 60)
    var seconds = seconds - (hours * 3600) - (minutes * 60)
    var time = ""

    if (hours != 0) {
      time = hours+":"
    }
    if (minutes != 0 || time !== "") {
      minutes = (minutes < 10 && time !== "") ? "0"+minutes : String(minutes)
      time += minutes+":"
    }
    if (time === "") {
      time = seconds+"s"
    }
    else {
      time += (seconds < 10) ? "0"+seconds : String(seconds)
    }
    return time
}


fetch('/config/get/general.security_level', {
    headers: {
        "token": webpass
    }})
    .then((resp) => resp.text()) // Transform the data into text
    .then(function(resp) {
        switch(resp){
                case "0":
                    sec_description_str = 'normal'
                    break;
                case "1":
                    sec_description_str = 'high'
                    break;
                case "2":
                    sec_description_str = 'very high'
                    break;
                case "3":
                    sec_description_str = 'extreme'
                    break;
            }
            if (sec_description_str !== 'normal'){
                showSecStatNotice()
            }
        })

var getStats = function(){
    if (document.hidden){
        console.debug('skipping stats since no window focus')
        return
    }
    fetch('/getstats', {
        headers: {
            "token": webpass
        }})
        .then((resp) => resp.json())
        .then(function(stats) {
            uptimeDisplay.innerText = seconds2time(stats['uptime'])
            connectedNodes = stats['connectedNodes'].split('\n')
            document.getElementById('connectedNodesIframe').srcdoc = '<pre>'
            for (x = 0; x < connectedNodes.length; x++){
                if (! x){
                    continue
                }
                document.getElementById('connectedNodesIframe').srcdoc += '🧅 ' + connectedNodes[x] + '\n'
            }
            document.getElementById('connectedNodesIframe').srcdoc += '</pre>'
            storedBlockDisplay.innerText = stats['blockCount']
            queuedBlockDisplay.innerText = stats['blockQueueCount']
            document.getElementById('threads').innerText = stats['threads']
            document.getElementById('ramPercent').innerText = (stats['ramPercent']).toFixed(2) + '%'
            document.getElementById('fileDescriptors').innerText = stats['fd']
            document.getElementById('diskUsage').innerText = stats['diskUsage']
            securityLevel.innerText = sec_description_str
            fetch('/hitcount', {
                headers: {
                    "token": webpass
                }})
                .then((resp) => resp.text())
                .then(function(resp) {
                    totalRec.innerText = resp
                })
            fetch('/lastconnect', {
                headers: {
                    "token": webpass
                }})
                .then((resp) => resp.text())
                .then(function(conn) {
                    var lastConnect = conn
                    if (lastConnect > 0){
                        var humanDate = new Date(0)
                        humanDate.setUTCSeconds(conn)
                        humanDate = humanDate.toString()
                        lastConnect = humanDate.substring(0, humanDate.indexOf('('));
                    }
                    else{
                        lastConnect = 'None since start'
                    }
                    lastIncoming.innerText = lastConnect
                })
        })
}

document.addEventListener("visibilitychange", function() {
    if (document.visibilityState === 'visible') {
      getStats()
    }
  })

getStats()
statsInterval = setInterval(function(){getStats()}, 1000)



fetch('/config/get/ui.animated_background', {
    headers: {
        "token": webpass
    }})
    .then((resp) => resp.text()) // Transform the data into text
    .then(function(resp) {
        if (resp == "false"){
            return
        }
        fetch('/config/get/ui.theme', {
            headers: {
                "token": webpass
            }})
            .then((resp) => resp.text()) // Transform the data into text
            .then(function(resp) {
                if (resp == '"dark"'){
                    /* particlesJS.load(@dom-id, @path-json, @callback (optional)); */
                    particlesJS.load('particles-js', '/shared/main/particles.json', function() {
                        console.debug('callback - particles.js config loaded')
                    })
                }
            }
        )
    }
    )