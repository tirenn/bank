package service

import (
	"context"

	"bank-core/internal/domain"
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

