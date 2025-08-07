import asyncio
from asyncio import Task
from icmplib import async_ping,Host,async_multiping as multiPing
from typing import List,Dict
from source.PingStats import PingStats

class Controller():    
    def __init__(self):
        self.addresses:List[str] = []
        self.count=1
        self.interval=1000 #ms
        self.timeout=1
        self.concurrent_tasks=50
        self.byteSize = 56
        #self.loop = asyncio.get_running_loop()
        self.tasks: List[Task] = []

        self.tasks_pending = set()        
        self.tasks_dict: Dict[str, Task[Host]] = {}
        self.pingStatList: List[PingStats] = []

    
    async def startPing(self):
       """ asyncio.run(self.async_multiping(
            addresses=self.addresses,
            interval=self.interval / 1000,
            timeout=self.timeout,
            concurrent_tasks=self.concurrent_tasks
        ))"""
       asyncio.run(multiPing(self.addresses,interval=self.interval, timeout=self.timeout,concurrent_tasks=100))
       

    

    def ipfinder_on_task_pending(self, address:str):
        for task in self.tasks:
            if address == task.get_name():
                return task

    def add_addresses(self, addreses:List[str]):
        for address in addreses:
            self.addresses.append(address)
        
    def stop_task(self,task: Task):
        pass
    def get_PingStatsList(self):
        return self.pingStatList
    
    