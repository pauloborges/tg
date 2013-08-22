# coding: utf-8

from powermeter.arduino import Arduino
import powermeter.gui as gui

modes = {
    "inst":  "I",
    "agreg": "A",
}

WIN_SIZE = (1000, 600)

def run(action, mode, **kwargs):
    app, win = gui.init(WIN_SIZE, action)

    f = snapshot if action == "snapshot" else monitor
    gui.single_shot(f, win=win, mode=mode, **kwargs)

    app.exec_()

def create_inst_graphs(win):
    voltage_plt = win.addPlot()
    current_plt = win.addPlot()
    win.nextRow()
    realpower_plt = win.addPlot()

def create_agreg_graphs(win):
    pass

def update_inst_graphs(sample, graphs):
    pass

def update_agreg_graphs(sample, graphs):
    pass

def snapshot(win, mode, waves, cycles, fake):
    if mode == "inst":
        graphs = create_inst_graphs(win)
        update = update_inst_graphs
    else:
        graphs = create_agreg_graphs(win)
        update = update_agreg_graphs

    with Arduino() as arduino:
        mode = modes[mode]
        ok = arduino.snapshot(mode, waves, cycles, fake)

        if not ok:
            raise IOError("Arduino refused to snapshot")

        for sample in arduino.samples():
            # print "INST SAMPLE:", sample
            update(sample, graphs)

def monitor(win, mode, waves, fake):
    if mode == "inst":
        graphs = create_inst_graphs(win)
        update = update_inst_graphs
    else:
        graphs = create_agreg_graphs(win)
        update = update_agreg_graphs

    with Arduino() as arduino:
        mode = modes[mode]
        ok = arduino.monitor(mode, waves, fake)

        if not ok:
            raise IOError(u"Arduino refused to monitor")

        try:
            for sample in arduino.samples():
                update(sample, graphs)

        except KeyboardInterrupt:
            pass
