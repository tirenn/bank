package service

import (
	"context"
	"errors"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
)

type aiModelService struct {
	repo domain.AIModelRepository
}

func NewAIModelService(repo domain.AIModelRepository) domain.AIModelService {
	return &aiModelService{repo: repo}
}

func (s *aiModelService) GetActiveModels(ctx context.Context) (*domain.AIModelResponse, error) {
	models, err := s.repo.GetActive(ctx)
	if err != nil {
		return nil, err
	}

	slugs := make([]string, 0, len(models))
	for _, m := range models {
		slugs = append(slugs, m.ModelID)
	}

	defaultModel := ""
	if len(slugs) > 0 {
		defaultModel = slugs[0]
	}

	return &domain.AIModelResponse{
		Models:       slugs,
		DefaultModel: defaultModel,
		Details:      models,
	}, nil
}

func (s *aiModelService) ListAllModels(ctx context.Context) ([]domain.AIModel, error) {
	return s.repo.ListAll(ctx)
}

func (s *aiModelService) CreateModel(ctx context.Context, req *domain.CreateAIModelRequest) (*domain.AIModel, error) {
	if req.Name == "" || req.ModelID == "" {
		return nil, errors.New("name and model_id are required")
	}

	provider := req.Provider
	if provider == "" {
		provider = "openrouter"
	}

	priority := req.Priority
	if priority <= 0 {
		priority = 10
	}

	model := &domain.AIModel{
		Name:      req.Name,
		ModelID:   req.ModelID,
		Provider:  provider,
		IsFree:    req.IsFree,
		IsActive:  req.IsActive,
		Priority:  priority,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err := s.repo.Create(ctx, model); err != nil {
		return nil, err
	}

	logger.Info(ctx, "Created new AI model in database", map[string]interface{}{
		"model_id": model.ModelID,
		"priority": model.Priority,
	})
	return model, nil
}

func (s *aiModelService) UpdateModel(ctx context.Context, id uint64, req *domain.UpdateAIModelRequest) (*domain.AIModel, error) {
	model, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, err
	}

	if req.Name != nil {
		model.Name = *req.Name
	}
	if req.Provider != nil {
		model.Provider = *req.Provider
	}
	if req.IsFree != nil {
		model.IsFree = *req.IsFree
	}
	if req.IsActive != nil {
		model.IsActive = *req.IsActive
	}
	if req.Priority != nil {
		model.Priority = *req.Priority
	}
	model.UpdatedAt = time.Now()

	if err := s.repo.Update(ctx, model); err != nil {
		return nil, err
	}

	logger.Info(ctx, "Updated AI model in database", map[string]interface{}{
		"id":       model.ID,
		"model_id": model.ModelID,
	})
	return model, nil
}

func (s *aiModelService) DeleteModel(ctx context.Context, id uint64) error {
	return s.repo.Delete(ctx, id)
}
