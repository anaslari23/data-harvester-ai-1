"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { getCompanies, getCompany } from "@/services/companyService";
import type { CompanyFilters, CompanyRecord } from "@/types/company";

type CompanyState = {
  companies: CompanyRecord[];
  selectedCompany: CompanyRecord | null;
  filters: CompanyFilters;
  pageIndex: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  fetchCompanies: () => Promise<void>;
  fetchCompanyById: (id: string) => Promise<void>;
  setFilters: (filters: Partial<CompanyFilters>) => void;
  setPageIndex: (pageIndex: number) => void;
  setPageSize: (pageSize: number) => void;
  setSelectedCompany: (company: CompanyRecord | null) => void;
};

export const useCompanyStore = create<CompanyState>()(
  persist(
    (set) => ({
      companies: [],
      selectedCompany: null,
      filters: { search: "", industry: "all", erp: "all" },
      pageIndex: 0,
      pageSize: 20,
      loading: false,
      error: null,
      fetchCompanies: async () => {
        set({ loading: true, error: null });
        try {
          const companies = await getCompanies();
          set({ companies, loading: false });
        } catch (error) {
          set({
            companies: [],
            loading: false,
            error: error instanceof Error ? error.message : "Unable to load companies.",
          });
        }
      },
      fetchCompanyById: async (id) => {
        try {
          const company = await getCompany(id);
          set({ selectedCompany: company });
        } catch (error) {
          set({
            selectedCompany: null,
            error: error instanceof Error ? error.message : "Unable to load company details.",
          });
        }
      },
      setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters }, pageIndex: 0 })),
      setPageIndex: (pageIndex) => set({ pageIndex }),
      setPageSize: (pageSize) => set({ pageSize }),
      setSelectedCompany: (selectedCompany) => set({ selectedCompany }),
    }),
    {
      name: "dh-company-store-v2",
      partialize: (state) => ({
        companies: state.companies,
        filters: state.filters,
        pageIndex: state.pageIndex,
        pageSize: state.pageSize,
      }),
    },
  ),
);
