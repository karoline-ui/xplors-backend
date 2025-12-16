-- ========================================
-- XPLORS - SETUP DO BANCO DE DADOS SUPABASE
-- ========================================
-- 
-- Execute este script no SQL Editor do Supabase
-- https://supabase.com/dashboard/project/_/sql
--
-- ========================================

-- 1. Criar tabela de análises
CREATE TABLE IF NOT EXISTS analises (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tipo_analise VARCHAR(50) NOT NULL,
    total_linhas INTEGER NOT NULL,
    pdf_url TEXT NOT NULL,
    pdf_filename VARCHAR(255) NOT NULL,
    nome_arquivo_original VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Criar índices para performance
CREATE INDEX idx_analises_user_id ON analises(user_id);
CREATE INDEX idx_analises_created_at ON analises(created_at DESC);

-- 3. Habilitar Row Level Security (RLS)
ALTER TABLE analises ENABLE ROW LEVEL SECURITY;

-- 4. Políticas de segurança
-- Usuário só pode ver suas próprias análises
CREATE POLICY "Usuário vê apenas suas análises"
ON analises FOR SELECT
USING (auth.uid() = user_id);

-- Usuário só pode inserir análises para si mesmo
CREATE POLICY "Usuário insere apenas suas análises"
ON analises FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Usuário pode atualizar apenas suas análises
CREATE POLICY "Usuário atualiza apenas suas análises"
ON analises FOR UPDATE
USING (auth.uid() = user_id);

-- Usuário pode deletar apenas suas análises
CREATE POLICY "Usuário deleta apenas suas análises"
ON analises FOR DELETE
USING (auth.uid() = user_id);

-- 5. Criar bucket de storage para PDFs
-- Execute no Supabase Dashboard > Storage > Create Bucket
-- Nome: relatorios-pdf
-- Public: false (somente usuários autenticados)

-- ========================================
-- SUCESSO! ✅
-- ========================================
-- 
-- Próximos passos:
-- 1. Crie o bucket "relatorios-pdf" no Storage
-- 2. Configure as políticas de acesso do bucket:
--    - Allow authenticated users to upload
--    - Allow users to read their own files
--
-- ========================================
