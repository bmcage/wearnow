#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import time
from collections import deque

class DbUndo(object):
    """
    Base class for the Gramps undo/redo manager.  Needs to be subclassed
    for use with a real backend.
    """

    __slots__ = ('undodb', 'db', 'mapbase', 'undo_history_timestamp',
                 'txn', 'undoq', 'redoq')

    def __init__(self, grampsdb):
        """
        Class constructor. Set up main instance variables
        """
        self.db = grampsdb
        self.undoq = deque()
        self.redoq = deque()
        self.undo_history_timestamp = time.time()
        self.txn = None
        # N.B. the databases have to be in the same order as the numbers in
        # xxx_KEY in gen/db/dbconst.py
        self.mapbase = (
                        self.db.textile_map,
                        self.db.ensemble_map,
                        self.db.media_map,
                        self.db.note_map,
                        self.db.tag_map,
                        )

    def clear(self):
        """
        Clear the undo/redo list (but not the backing storage)
        """
        self.undoq.clear()
        self.redoq.clear()
        self.undo_history_timestamp = time.time()
        self.txn = None

    def __enter__(self, value):
        """
        Context manager method to establish the context
        """
        self.open(value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager method to finish the context
        """
        if exc_type is None:
            self.close()
        return exc_type is None

    def open(self, value):
        """
        Open the backing storage.  Needs to be overridden in the derived
        class.
        """
        raise NotImplementedError

    def close(self):
        """
        Close the backing storage.  Needs to be overridden in the derived
        class.
        """        
        raise NotImplementedError

    def append(self, value):
        """
        Add a new entry on the end.  Needs to be overridden in the derived
        class.
        """        
        raise NotImplementedError

    def __getitem__(self, index):
        """
        Returns an entry by index number.  Needs to be overridden in the
        derived class.
        """        
        raise NotImplementedError

    def __setitem__(self, index, value):
        """
        Set an entry to a value.  Needs to be overridden in the derived class.
        """           
        raise NotImplementedError

    def __len__(self):
        """
        Returns the number of entries.  Needs to be overridden in the derived
        class.
        """         
        raise NotImplementedError

    def __redo(self, update_history):
        """
        """
        raise NotImplementedError

    def __undo(self, update_history):
        """
        """
        raise NotImplementedError

    def commit(self, txn, msg):
        """
        Commit the transaction to the undo/redo database.  "txn" should be
        an instance of Gramps transaction class
        """
        txn.set_description(msg)
        txn.timestamp = time.time()
        self.undoq.append(txn)

    def undo(self, update_history=True):
        """
        Undo a previously committed transaction
        """
        if self.db.readonly or self.undo_count == 0:
            return False
        return self.__undo(update_history)

    def redo(self, update_history=True):
        """
        Redo a previously committed, then undone, transaction
        """
        if self.db.readonly or self.redo_count == 0:
            return False
        return self.__redo(update_history)

    def undo_reference(self, data, handle, db_map):
        """
        Helper method to undo a reference map entry
        """
        try:
            if data is None:
                db_map.delete(handle, txn=self.txn)
            else:
                db_map.put(handle, data, txn=self.txn)

        except DBERRS as msg:
            self.db._log_error()
            raise DbError(msg)

    def undo_data(self, data, handle, db_map, emit, signal_root):
        """
        Helper method to undo/redo the changes made
        """
        try:
            if data is None:
                emit(signal_root + '-delete', ([handle2internal(handle)],))
                db_map.delete(handle, txn=self.txn)
            else:
                ex_data = db_map.get(handle, txn=self.txn)
                if ex_data:
                    signal = signal_root + '-update'
                else:
                    signal = signal_root + '-add'
                db_map.put(handle, data, txn=self.txn)
                emit(signal, ([handle2internal(handle)],))

        except DBERRS as msg:
            self.db._log_error()
            raise DbError(msg)

    undo_count = property(lambda self:len(self.undoq))
    redo_count = property(lambda self:len(self.redoq))