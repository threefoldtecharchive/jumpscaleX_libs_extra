from Jumpscale import j

JSBASE = j.baseclasses.object


class StatManager(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)
        self.inited = False
        self.historyObjs = {}
        self.historyObjsMod = {}
        self.historyObjsLastSave = {}
        self._hourseconds = float(60 * 60)
        self._dayseconds = float(24 * 60 * 60)
        self._monthseconds = float(31 * self._dayseconds)
        self.now = None
        self.hourId = None
        self.fiveMinuteId = None

    def getFiveMinuteId(self):
        if self.fiveMinuteId is not None:
            return self.fiveMinuteId
        else:
            return j.data.time.get5MinuteId()

    def getHourId(self):
        if self.hourId is not None:
            return self.hourId
        else:
            return self.base.time.getHourId()

    def scheduleSaveClean(self):
        j.portal.server.active.addSchedule1MinPeriod("saveInfomgr", self.save)
        j.portal.server.active.addSchedule15MinPeriod("cleanCacheInfoMgr", self.cleanCache)

        # per hour we keep: nritems,maxitem,minitem,total  (so out of this we can calc average)

        # REMARK: now we do all in mem, in future we will have to cache the incoming values and only process couple of objects per time
        #   only when a request for info comes we need to process the info for that object first

    def reset(self):
        # self.models.infotable.destroy()
        # self.models.history.destroy()
        # from IPython import embed
        # print "DEBUG NOW osis destroy"
        # embed()

        self.historyObjs = {}
        self.historyObjsMod = {}
        self.historyObjsLastSave = {}
        self.infotableLastSave = self.getEpoch()

    def getNrItemsRow(self, key):
        """
        """
        if key.find("counter") != -1:
            nrItemsIn5MinRow = 0  # no need to stor per 5 min
            nrItemsInHourRow = 1464  # only keep 2 months (keep 61 days)
            return nrItemsIn5MinRow, nrItemsInHourRow
        else:
            nrItemsIn5MinRow = 8929  # 2 months (32 days so more than 1 month)
            nrItemsInHourRow = 8761  # 1 year+1h
            return nrItemsIn5MinRow, nrItemsInHourRow

    def save(self, force=False):
        self.hourId = self.base.time.getHourId()
        self.fiveMinuteId = j.data.time.get5MinuteId()

        ttime = self.getEpoch()
        now5min = j.portal.server.active.fiveMinuteId
        nowh = j.portal.server.active.hourId
        # walk over history obj and save if needed
        for key in list(self.historyObjs.keys()):
            if force or ttime > (self.historyObjsLastSave[key] + 900):
                if key in self.historyObjsMod and self.historyObjsMod[key]:
                    obj = self.historyObjs[key]
                    nrItemsIn5MinRow, nrItemsInHourRow = self.getNrItemsRow(key)
                    self._log_debug(("save: %s" % (obj.guid)))
                    # trim values out of range
                    if nrItemsIn5MinRow != 0:
                        test = now5min - nrItemsIn5MinRow
                        if min(obj.month_5min.keys()) < test:
                            # remove old items for 5min
                            for key in list(obj.month_5min.keys()):
                                if key < test:
                                    obj.month_5min.pop(key)
                    else:
                        obj.month_5min = {}
                    if nrItemsInHourRow != 0:
                        test = nowh - nrItemsInHourRow
                        if min(obj.year_hour.keys()) < test:
                            # remove old items for 5min
                            for key in list(obj.year_hour.keys()):
                                if key < test:
                                    obj.year_hour.pop(key)
                    else:
                        obj.year_hour = {}

                    self._save(key, obj)

    def _save(self, key, obj):
        data = self._serialize(obj)
        self.models.history.set(data)
        self.historyObjsLastSave[key] = ttime
        self.historyObjsMod[key] = False

    def _serialize(self, key, obj):
        # TODO: needs to be implemented, go to dense binary format (use struct)
        return obj

    def _deserialize(self, data):
        return data

    def cleanCache(self):
        self._log_debug("clean cache")
        ttime = self.getEpoch()
        try:
            for key in list(self.historyObjs.keys()):
                if self.historyObjsMod[key] is False and ttime > (self.historyObjsLastSave[key] + 600):
                    self.historyObjs.pop(key)
                    self.historyObjsLastSave.pop(key)
                    self.historyObjsMod.pop(key)
        except Exception as e:
            # from IPython import embed
            # print "DEBUG NOW error in clean cache for StatManager"
            # embed()
            pass

    def getEpoch(self):
        if self.now is not None:
            return self.now
        else:
            return j.data.time.getTimeEpoch()

    def getHistoryObject(self, id):
        if id in self.historyObjs:
            return self.historyObjs[id]
        # now = self.getEpoch()
        # from IPython import embed
        # print "DEBUG NOW getmodel"
        # embed()

        data = self.models.history.get(guid=id, createIfNeeded=True)
        obj = self._deserialize(data)
        # if obj.month_5min=={}:
        #     for i in range(8928):
        # nrsecondsago=i*5*60 #(every 5 min)
        #         key=j.data.time.get5MinuteId(now-nrsecondsago)
        #         obj.month_5min[key]=0
        self.historyObjs[id] = obj
        self.historyObjsLastSave[id] = self.getEpoch()

        return self.historyObjs[id]

    def _getKey5min(self, epoch):
        # nrsecondsago=5*60
        return j.data.time.get5MinuteId(epoch)

    def addInfoLine2HistoryObj(self, id, value, epoch=None):
        if epoch is None:
            epoch = self.getEpoch()
        obj = self.getHistoryObject(id)
        key = j.data.time.get5MinuteId(epoch)
        key2 = j.data.time.getHourId(epoch)

        # store 5min value
        obj.month_5min[key] = value

        # remember modification
        self.historyObjsMod[id] = True

        # value for hour row
        if key2 in obj.year_hour:
            nritems, total, mmin, mmax = obj.year_hour[key2]
            if value < mmin:
                mmin = value
            if value > mmax:
                mmax = value
            total += value
            nritems += 1
            obj.year_hour[key2] = (nritems, total, mmin, mmax)
        else:
            obj.year_hour[key2] = (1, value, value, value)

        # cleanup is not done here but when we save the object to the keyval stor

    def listHistoryObjects(self):
        result = []
        for item in self.models.history.list():
            if item.find(".") != -1:
                result.append(item)
        return result

    def addInfo(self, info):
        """
        can be multi line
        param:info dotnotation of info e.g. 'water.white.level.sb 10'  (as used in graphite)
        result bool
        """
        now = self.getEpoch()
        for line in info.split("\n"):
            if line.strip() == "":
                continue
            splitted = line.split(" ")
            if len(splitted) == 3:
                id, value, epoch = splitted
                epoch = int(epoch)
            elif len(splitted) == 2:
                id, value = splitted
                epoch = now
            else:
                j.errorhandler.raiseMonitoringError(
                    "Line '%s' not well constructed, cannot process monitoring stat info", id
                )
                continue
            id = str(id.lower())
            if value.find(".") != -1:
                value = float(value)
            else:
                value = int(value)
            # # make sure table of stats is complete
            # if id not in self.infotable:
            #     self.infotable[id] = True
            #     print "infotable NEW"
            #     self.models.infotable.set(self._infotableobj)

            self.addInfoLine2HistoryObj(id, value, epoch)

    def resampleList(self, llist, nritems=200):
        l = len(llist)
        if l > nritems:
            skip = int((float(l) / nritems))
        else:
            skip = 1
        pos = 1
        r = []
        for item in llist:
            if skip == pos:
                r.append(item)
                pos = 0
            pos += 1
        return r

    def getInfoWithHeaders(self, id, start, stop, maxvalues):
        """
        param:id id in dot noation e.g. 'water.white.level.sb'  (can be multiple use comma as separation)
        param:start epoch
        param:stop epoch
        param:maxvalues nr of values you want to return
        result list(list)

        """
        if id is None:
            id = ""
        if id.find(",") != -1:
            ids = id.split(",")
        else:
            ids = [id]
        rows = []
        for id in ids:
            row = self.getInfo5MinFromTo(id, start, stop)
            row = self.resampleList(row, nritems=maxvalues)
            rows.append(row)
        header = self.getHeaders(start, stop)
        header = self.resampleList(header, nritems=maxvalues)
        return [header, rows]

    def getHeaders(self, start, stop):
        start = self.getTimeStamp(start)
        stop = self.getTimeStamp(stop)
        start2 = j.data.time.get5MinuteId(start)
        stop2 = j.data.time.get5MinuteId(stop) - start2
        start2 = 0
        hoursecs = 60 * 60 / 5
        r = []
        if (stop - start) < self._hourseconds:
            for i in range(start2, stop2 + 1):
                r.append("%sm" % i * 5)
        elif (stop - start) < self._dayseconds:
            for i in range(start2, stop2 + 1):
                i2 = int(float(i) / 12)
                r.append("%sh" % i2)
        else:
            for i in range(start2, stop2 + 1):
                i2 = int(float(i) / (12 * 24))
                r.append("%sd" % i2)
        r.reverse()
        return r

    def getTimeStamp(self, timestamp):
        if isinstance(timestamp, str):
            timestamp = j.data.time.getEpochAgo(timestamp)
        return timestamp

    def getInfo5MinFromTo(self, id, start, stop):
        """
        will not return more than 1 month of info
        param:id id in dot noation e.g. 'water.white.level.sb'
        param:start epoch
        param:stop epoch
        result list with values

        """
        obj = self.getHistoryObject(id)
        start2 = j.data.time.get5MinuteId(self.getTimeStamp(start))
        stop2 = j.data.time.get5MinuteId(self.getTimeStamp(stop))
        r = []
        for i in range(start2, stop2 + 1):
            if i in obj.month_5min:
                r.append(obj.month_5min[i])
            else:
                r.append(0)
        return r

    def getInfo1hFromTo(self, id, start, stop):
        """
        will not return more than 12 months of info, resolution = 1h
        param:id id in dot noation e.g. 'water.white.level.sb'
        param:start epoch
        param:stop epoch
        result dict()

        """
        pass

    def getInfo5Min(self, id, start=0, stop=0, epoch2human=False):
        """
        return raw info (resolution is 5min)
        param:id id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        param:start epoch; 0 means all
        param:stop epoch; 0 means all
        result list(list)  [[epoch,value],[epoch,value],...]

        """
        result = []
        obj = self.getHistoryObject(id)
        if len(list(obj.month_5min.keys())) == 0:
            result.append([])
            return None
        if start == 0:
            start2 = min(obj.month_5min.keys())
        else:
            start2 = j.data.time.get5MinuteId(start)
        if stop == 0:
            stop2 = max(obj.month_5min.keys())
        else:
            stop2 = j.data.time.get5MinuteId(stop)
        for key in range(stop2, start2, -1):
            epoch = j.data.time.fiveMinuteIdToEpoch(key)
            if epoch2human:
                epoch = j.data.time.epoch2HRDateTime(epoch)
            result.append([epoch, obj.month_5min[key]])
        return result

    def getInfo1h(self, id, start, stop):
        """
        return raw info (resolution is 1h)
        param:id id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        param:start epoch; 0 means all
        param:stop epoch; 0 means all
        result list(list)

        """
        pass
