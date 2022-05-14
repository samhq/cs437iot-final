var app = new Vue({
    el: '#app',
    data() {
        return {
            selectedDevice: {},
            backendSrc: "http://192.168.0.110:5000",
            links: ["History", "Settings", "Live Feed"],
            selectedLink: "",
            devices: [],
            newDevice: {
                id: "",
                name: "",
                liveFeed: "",
                apiUrl: ""
            },
            title: "Smart Greetings and Security System",
            defaultTitle: "Smart Greetings and Security System",
            history: [{
                    name: "x",
                    image: "https://via.placeholder.com/640x360.png",
                    date: "2022-05-13 18:12:48"
                },
                {
                    name: "y",
                    image: "https://via.placeholder.com/640x360.png",
                    date: "2022-05-13 16:02:25"
                },
                {
                    name: "z",
                    image: "https://via.placeholder.com/640x360.png",
                    date: "2022-05-13 09:11:07"
                },
            ],
            currentSettings: "",
            personNameToRename: "",
            fileToRename: ""
        }
    },
    filters: {
        pretty: (val, indent = 2) => {
            return JSON.stringify(JSON.parse(val), null, indent);
        }
    },
    mounted() {
        this.getDevices()
        this.home()
    },
    methods: {
        getDevices() {
            axios.get(this.backendSrc + '/devices')
                .then(response => (this.devices = response.data.data))
        },
        addNewDevice() {
            axios.post(this.backendSrc + '/devices', {
                    id: this.newDevice.id,
                    name: this.newDevice.name,
                    liveFeed: this.newDevice.liveFeed,
                    apiUrl: this.newDevice.apiUrl
                })
                .then(response => (this.getDevices()))

            this.newDevice.id = ""
            this.newDevice.name = ""
            this.newDevice.liveFeed = ""
            this.newDevice.apiUrl = ""
        },
        deleteDevice(deviceId) {
            console.log("delete", deviceId)
            axios.post(this.backendSrc + '/devices/delete', {
                    id: deviceId
                })
                .then(response => (this.getDevices()))
        },

        manageDevice(device) {
            console.log("manage", device)
            this.title = device.name
            this.selectedDevice = device
            this.selectLink(this.links[0])
        },

        home() {
            this.title = this.defaultTitle
            this.selectedDevice = {}
            this.selectedLink = ""
            this.currentSettings = ""
            this.history = []
            this.personNameToRename = ""
            this.fileToRename = ""
        },

        selectLink(link) {
            console.log("select link", link)
            this.selectedLink = link
            if (link == this.links[0]) {
                // history
                this.getHistory(this.selectedDevice.id)
            } else if (link == this.links[1]) {
                //settings
                this.getSettings(this.selectedDevice.id)
            } else if (link == this.links[2]) {
                // live feed

            }
        },

        getHistory(deviceId) {
            console.log("get Settings", deviceId)
            axios.get(this.backendSrc + '/history/' + deviceId)
                .then(response => ( this.history = response.data.data ))
        },

        getSettings(deviceId) {
            console.log("get Settings", deviceId)
            axios.get(this.backendSrc + '/settings/' + deviceId)
                .then(response => (this.currentSettings = response.data.data))
        },

        saveSettings(deviceId) {
            console.log("save Settings", deviceId)
            axios.post(this.backendSrc + '/settings/' + deviceId, {
                    settings: this.currentSettings
                })
                .then(response => (console.log(response)))
        },

        renameFilename(name, image) {
            this.personNameToRename = name
            imgs = image.split("/")
            this.fileToRename = imgs[imgs.length - 1]
        },

        updateFilename(deviceId) {
            console.log(deviceId, this.personNameToRename, this.fileToRename)
            axios.post(this.backendSrc + '/images/rename/' + deviceId +'/'+this.fileToRename, {
                updated_name: this.personNameToRename
            })
            .then(response => (console.log(response)))
            this.personNameToRename = ""
            this.fileToRename = ""

            this.selectLink(this.links[0])
        }
    }
})
