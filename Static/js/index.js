new Vue({
    el: "#form_container",
    data() {
      return {
        mode: "1", // 模式：定时下单/有货自动下单
        date: "",
        area: "", // 所在地区
        skurl: "", // 商品url
        count: "1", // 购买数量
        retry: "10", // 重试次数
        work_count: "1", // 启动线程数
        timeout: "30", // 超时时间
        eid: "",
        fp: "",
        timeSelectAble: true,
        dialogVisible: false,
        dialog: "",
        skuid: "",
        qrUrl: "./img/qr_code.png",
        qrVisible: false,
        qrReq: undefined,
        qrID: 0,
        qrReset: true,
        title: "错误",
        task: true
      };
    },
    mounted() {
      this.getEidFp()
      setTimeout(() => {
        this.main()
      }, 100)
    },
    methods: {
      main() {
      },
      upload() {
        if (!this.checkValid()) return
        let url = "0.0.0.0:12021/api/jd-shopper"
        let data = {
          mode: this.mode,
          date: this.date,
          area: this.area,
          skuid: this.skuid,
          count: this.count,
          retry: this.retry,
          work_count: this.work_count,
          timeout: this.timeout,
          eid: this.eid,
          fp: this.fp,
        };
        fetch(url, {
          body: JSON.stringify(data), // must match 'Content-Type' header
          cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
          credentials: 'same-origin', // include, same-origin, *omit
          headers: {
            'user-agent': 'Mozilla/4.0 MDN Example',
            'content-type': 'application/json'
          },
          method: 'POST', // *GET, POST, PUT, DELETE, etc.
          mode: 'cors', // no-cors, cors, *same-origin
          redirect: 'follow', // manual, *follow, error
          referrer: 'no-referrer', // *client, no-referrer
        }).then(response => {
          return response.json()
        }).then(res => {
          console.log(res)
            setTimeout(() => {
              this.qrShow()
              this.loginCheck()
            }, 200)
        })
      },
      buyMode(value) {
        if (this.mode === "1" || this.mode === 1) {
          this.timeSelectAble = true;
        } else {
          this.timeSelectAble = false;
        }
      },
      getEidFp() {
        let that = this
        setTimeout(() => {
          try {
              getJdEid(function (eid, fp, udfp) {
                  that.eid = eid
                  that.fp = fp
              });
          } catch (e) {
              that.dialogShow("获取eid与fp失败，请手动获取。")
          }
        }, 0);
      },
      reset() {
        this.mode = "1" // 模式：定时下单/有货自动下单
        this.date = ""
        this.area = "" // 所在地区
        this.skurl = "" // 商品url
        this.count = "1" // 购买数量
        this.retry = "10" // 重试次数
        this.work_count = "1" // 启动线程数
        this.timeout = "3" // 超时时间
        this.eid = ""
        this.fp = ""
      },
      dialogShow(mes) {
        this.dialog = mes
        this.dialogVisible = true
      },
      checkValid() {
        if (this.area == "" || this.skurl == "") {
          this.dialogShow("地区ID与商品链接不能为空")
          return false
        }
        else if (this.mode == "2" && this.date == "") {
          this.dialogShow("定时下单需设置时间")
          return false
        }
        let skuid = this.skurl.match(new RegExp(`https://item.jd.com/(.*?).html`))
        skuid = skuid ? skuid[1] : null
        if (skuid == null) {
          skuid= this.skurl.replace(/[^0-9]/ig,"")
          reNum = /^[0-9]+.?[0-9]*/
          if (!reNum.test(skuid)) { 
            this.dialogShow("请输入正确的网址")
            return false
          }
        }
        this.skuid = skuid
        return true
      },
      qrShow() {
        this.qrVisible = true
        this.qrID = 0
        
        
        this.qrReq = setInterval(function () {
          let imgDiv = document.getElementsByClassName("el-image")[0]
          imgDiv.removeChild(imgDiv.childNodes[0])
          this.qrID++
          this.qrUrl = './img/qr_code.png'
          this.qrReset = false
        }, 3000)
      },

      loginCheck() {
        let url = './api/jd-login-status'
        let loginReq = setInterval(() => {
          let imgDiv = document.getElementsByClassName("el-image")[0]
          imgDiv.innerHTML = `<img src="./img/qr_code.png?id={this.qrID}" class="el-image__inner">`
          fetch(url)
          .then(response => {
            return response.json();
          })
          .then(res => {
            console.log(res);
            if (res.data) {
              this.qrVisible = false
              clearInterval(this.qrReq)
              clearInterval(loginReq)
              this.getLog()
              this.task = false
            }
          });
        }, 1000)
      },
      getLog() {
        let url = './api/log'

        fetch(url)
        .then(response => {
          return response.json();
        })
        .then(res => {
          console.log(res.data);
          document.getElementById('log').innerHTML = res.data
        });

        setInterval(() => {
          fetch(url)
          .then(response => {
            return response.json();
          })
          .then(res => {
            console.log(res.data);
            document.getElementById('log').innerHTML = res.data
          });
        }, 10000)
      }
    },
  });


  // confirm,e.prototype.$prompt=ya.prompt,e.prototype.$notify=tl,e.prototype.$message=ou};
//"undefined"!=typeof window&&window.Vue&&Ld(window.Vue);t.default={version:"2.15.0",
//locale:j.use,i18n:j.i18n,install:Ld,CollapseTransition:ii,Loading:_l,Pagination:pt,
//Dialog:gt,Autocomplete:kt,Dropdown:At,DropdownMenu:Bt,DropdownItem:Wt,Menu:ei,
//Submenu:ai,MenuItem:di,MenuItemGroup:vi,Input:ne,InputNumber:_i,Radio:Si,RadioGroup:Mi,
//RadioButton:Ii,Checkbox:Vi,CheckboxButton:Ri,CheckboxGroup:Yi,Switch:Xi,Select:ct,
//Option:ht,OptionGroup:en,Button:Et,ButtonGroup:Pt,Table:Un,TableColumn:ir