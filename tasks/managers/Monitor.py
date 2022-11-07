from ... import app, utils

from multiprocessing import Process
from collections import defaultdict as dd 
from pathlib import Path 
from typing import Optional
from tqdm import tqdm

# Necessary to undo whatever issues tqdm causes with ansi codes
import colorama
colorama.deinit() 

import multiprocessing, datetime, json, traceback
import numpy as np 

try:    import plotext as plt 
except: plt = None



class Monitor:
    def __init__(self, 
        data        : list, 
        ac_methods  : list,
        timeout     : Optional[int] = None, # Seconds to wait for graceful exit
    ):
        self.n_data  = len(data)
        self.n_ac    = len(ac_methods)
        self.timeout = timeout
        self.process = None

    # Alternative to context manager __exit__
    def close(self):   return self._stop_process()

    # Context managers
    def __enter__(self, *args, **kwargs): return self._start_process()
    def  __exit__(self, *args, **kwargs): return self._stop_process()

    # Cannot read from Monitor
    def  __iter__(self): return



    def _start_process(self):
        if self.n_data == 0: return self
        self.process = Process(target=start_monitor, args=(self.n_data, self.n_ac))
        self.process.start()
        return self


    def _stop_process(self, *args, **kwargs):
        if self.process is None: return

        # Attempt to gracefully stop monitoring process
        try:
            self.process.join(timeout=self.timeout)
            self.process = None

        # Force kills if we weren't able to gracefully exit
        finally: self._kill_process()



    def _kill_process(self):
        if self.process is not None:
            getattr(self.process, 'kill', self.process.terminate)()
            self.process = None




@utils.catch_and_log('monitor_args_err.txt')
def extract_key(key: str, string: str):
    """ Extract the value associated with the given key in `string` """
    return string.split(f"'{key}': '")[-1].split("'")[0]



def start_monitor(total_samples, total_ac, show_plot=plt is not None):
    # https://vilya.pl/handling-celery-events/
    states = app.events.State()
    bars   = {}
    count  = {}

    ac_method_stats = {}
    if show_plot:
        plt.clt()
        plt.clc()


    @utils.catch_and_log('monitor_tracking_err.txt')
    def track_events(event):
        states.event(event)
        task  = states.tasks.get(event['uuid'])
        name  = (getattr(task, 'name', None) or 'search').split('.')[-1]
        label = lambda name: f'{name.title():>8} '
        state = getattr(event, 'state', getattr(task, 'state', 'Unknown'))

        if name == 'shutdown':
            return 

        if name == 'search' and state == 'SUCCESS':
            dataset = extract_key('dataset', task.args)
            uid     = extract_key('uid',     task.args)
            sensor  = task.args.split(" '")[-1][:-2] 
            outpath = task.kwargs.split('output_path=')[-1]
            outpath = outpath.split("('")[-1].split("')")[0]

            successful_search = str(task.result) != 'None'
            if dataset is not None:
                outpath = Path(outpath).joinpath(dataset, sensor)
                outpath.mkdir(exist_ok=True, parents=True)
                with outpath.joinpath('completed.csv').open('a+') as f:
                    f.write(f'{uid}, {successful_search}\n')

        else: successful_search = True 

        count_updates = [(name, count)]
        if name == 'correct':
            ac_method = extract_key('ac_method', task.kwargs)
            count_updates += [(ac_method, ac_method_stats)]

        for key, count_dict in count_updates:
            if key not in count_dict:
                count_dict[key] = dd(int)

            if state in ['RECEIVED']:
                count_dict[key]['Pending'] += 1
            elif state in ['STARTED']:
                count_dict[key]['Pending'] = max(0, count_dict[key]['Pending'] - 1)
                count_dict[key]['Running'] += 1
            elif state in ['SUCCESS', 'FAILURE']:
                count_dict[key]['Running'] = max(0, count_dict[key]['Running'] - 1)
                count_dict[key][state.title()] += int(successful_search) 


        x = list(count.keys())
        e = sorted(list(set([e for events in count.values() for e in events])), reverse=True)
        y = [[count[name][event] for name in x] for event in e]

        colors = {
            'Success'  : 'green',
            'Running'  : 'blue',
            'Pending'  : 'cyan',
            'Failure'  : 'red',
        }

        if show_plot:
            print()
            plt.cld()

            # plt.stacked_bar(list(map(label, x)), y, label=e, color=[colors[event] for event in e])
            y = np.array(y)
            total_y = np.zeros_like(y)
            for idx, series in enumerate(y):
                total_y[idx] = series + total_y[idx-1]

            acs = sorted(ac_method_stats)
            max_split = 6 # This is going to change based on how many ac processors / api sources have been encountered
            for idx, series in enumerate(total_y[::-1]):
                s_state = e[::-1][idx]
                s_color = colors[s_state]

                # pull out multi-bar groups
                if 'correct' in count:
                    series[x.index('correct')] = 0#np.nan
                plt.bar(np.arange(len(count)) + 0.5, series, label=s_state, color=s_color, width=.8, orientation='horizontal')

                # plot each group member state separately
                if 'correct' in count:
                    frac = 0.5 / len(ac_method_stats)
                    plt.bar(np.arange(len(ac_method_stats)) * 1/len(ac_method_stats) + x.index('correct') + frac, [ac_method_stats[ac][s_state] for ac in acs], color=s_color, width=.8 / len(ac_method_stats), orientation='horizontal') 

            # plot labels
            if 'correct' in count:
                frac = 0.5 / len(ac_method_stats)
                [plt.text(ac.strip("'"), x=sum(ac_method_stats[ac].values()) * 1.25, y=i * 1/len(ac_method_stats) + x.index('correct') + frac, alignment='left') for i, ac in enumerate(acs)]
            
            plt.yticks(np.arange(len(count)) + 0.5, list(map(label, x)))
            plt.ylim(0, len(count))
            plt.xlim(0, max(map(sum, [[count[name][event] for event in e] for name in x])))
            plt.xfrequency(5)
            plt.plotsize(70, 40)
            plt.show()
            plt.sleep(0.1)


        if name not in bars:
            total = total_samples * (1 if name == 'search' else total_ac)
            bars[name] = {
                'main'     : tqdm(total=total, position=len(bars)+(3 if show_plot else 0), desc=label(name)), 
                # 'main'     : tqdm(total=total * 3, position=len(bars) * 4, desc=label(name)), 
                # 'RECEIVED' : tqdm(total=total, position=len(bars) * 4 + 1, desc='    Received'), 
                # 'STARTED'  : tqdm(total=total, position=len(bars) * 4 + 2, desc='    Started'), 
                # 'SUCCESS'  : tqdm(total=total, position=len(bars) * 4 + 3, desc='    Finished'), 
            }
        if state in ['SUCCESS']: 
            bars[name]['main'].update(1)

        for name in bars:
            bars[name]['main'].display()
        if show_plot: plt.clt(lines=43)

    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
                'task-sent'      : track_events,
                'task-received'  : track_events,
                'task-started'   : track_events,
                'task-succeeded' : track_events,
                'task-failed'    : track_events,
                'task-rejected'  : track_events,
                'task-revoked'   : track_events,
                'task-retried'   : track_events,

                '*': states.event,
        })
        recv.handlers['stop-monitor'] = lambda event: setattr(recv, 'should_stop', True)
        recv.capture(limit=None, timeout=None, wakeup=True)

    for bar_dict in bars.values():
        for bar in bar_dict.values():
            bar.close()
    # if show_plot: plt.clt()
    


