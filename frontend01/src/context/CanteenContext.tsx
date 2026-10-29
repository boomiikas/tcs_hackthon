import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

export interface CanteenOption {
  id: string;
  name: string;
  location: string;
  daily_capacity: number;
  manager_name: string;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
}

interface CanteenContextType {
  selectedCanteen: string;
  setSelectedCanteen: (id: string) => void;
  canteens: CanteenOption[];
  currentDate: string;
  setCurrentDate: (date: string) => void;
  toasts: ToastMessage[];
  addToast: (message: string, type?: 'success' | 'warning' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
  unreadAlertCount: number;
  setUnreadAlertCount: (n: number) => void;
}

const CanteenContext = createContext<CanteenContextType | undefined>(undefined);

export const CanteenProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedCanteen, setSelectedCanteen] = useState<string>('canteen-1');
  const [canteens, setCanteens] = useState<CanteenOption[]>([
    { id: 'canteen-1', name: 'Central Student Commons', location: 'Main Campus Center, Block A', daily_capacity: 1400, manager_name: 'Priya Sharma' },
    { id: 'canteen-2', name: 'Engineering Quad Cafeteria', location: 'Tech Wing 3, Ground Floor', daily_capacity: 950, manager_name: 'David Chen' },
    { id: 'canteen-3', name: 'Graduate Hall Bistro', location: 'Grad Residence Quad, Tower C', daily_capacity: 600, manager_name: 'Amina Al-Mansoor' },
  ]);
  const [currentDate, setCurrentDate] = useState<string>('2026-10-29');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [unreadAlertCount, setUnreadAlertCount] = useState<number>(3);

  useEffect(() => {
    api.getCanteens()
      .then((data) => {
        if (data && data.length > 0) setCanteens(data);
      })
      .catch((err) => console.log('Using default canteens:', err));
  }, []);

  const addToast = (message: string, type: 'success' | 'warning' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => removeToast(id), 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <CanteenContext.Provider
      value={{
        selectedCanteen,
        setSelectedCanteen,
        canteens,
        currentDate,
        setCurrentDate,
        toasts,
        addToast,
        removeToast,
        unreadAlertCount,
        setUnreadAlertCount,
      }}
    >
      {children}
    </CanteenContext.Provider>
  );
};

export const useCanteen = () => {
  const context = useContext(CanteenContext);
  if (!context) throw new Error('useCanteen must be used within a CanteenProvider');
  return context;
};
