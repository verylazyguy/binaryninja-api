#pragma once

#include <QtCore/QAbstractItemModel>
#include <QtCore/QItemSelectionModel>
#include <QtWidgets/QListView>
#include <QtWidgets/QStyledItemDelegate>
#include "binaryninjaapi.h"
#include "dockhandler.h"
#include "viewframe.h"


struct BINARYNINJAUIAPI TagReference
{
	enum RefType
	{
		AddressTagRef,
		FunctionTagRef
	};
	
	TagRef tag;
	ArchitectureRef arch;
	FunctionRef func;
	RefType refType;
	uint64_t addr;
};


class BINARYNINJAUIAPI TagListModel: public QAbstractItemModel
{
	Q_OBJECT

	QWidget* m_owner;
	BinaryViewRef m_data;
	std::vector<TagReference> m_refs;

public:
	TagListModel(QWidget* parent, BinaryViewRef data);

	virtual QModelIndex index(int row, int col, const QModelIndex& parent) const override;
	virtual QModelIndex parent(const QModelIndex& i) const override;
	virtual bool hasChildren(const QModelIndex& parent) const override;
	virtual int rowCount(const QModelIndex& parent) const override;
	virtual int columnCount(const QModelIndex& parent) const override;
	virtual QVariant data(const QModelIndex& i, int role) const override;

	bool setModelData(const std::vector<TagReference>& refs, QItemSelectionModel* selectionModel, bool& selectionUpdated);
};


class BINARYNINJAUIAPI TagItemDelegate: public QStyledItemDelegate
{
	Q_OBJECT

	QFont m_font;
	int m_baseline, m_charWidth, m_charHeight, m_charOffset;

	void initFont();

public:
	TagItemDelegate(QWidget* parent);

	void updateFonts();

	virtual QSize sizeHint(const QStyleOptionViewItem& option, const QModelIndex& idx) const override;
	virtual void paint(QPainter* painter, const QStyleOptionViewItem& option, const QModelIndex& idx) const override;
};


class BINARYNINJAUIAPI TagList: public QListView, public DockContextHandler, public BinaryNinja::BinaryDataNotification
{
	Q_OBJECT
	Q_INTERFACES(DockContextHandler)

	ViewFrame* m_view;
	TagListModel* m_list;
	TagItemDelegate* m_itemDelegate;
	BinaryViewRef m_data;

	QTimer* m_hoverTimer;
	QPoint m_hoverPos;

	uint64_t m_curRefTarget = 0;
	bool m_navigating = false;
	bool m_navToNextOrPrevStarted = false;

protected:
	virtual void contextMenuEvent(QContextMenuEvent* event) override;
	virtual void keyPressEvent(QKeyEvent* e) override;
	virtual void mouseMoveEvent(QMouseEvent* e) override;
	virtual void mousePressEvent(QMouseEvent* e) override;
	virtual void notifyFontChanged() override;
	virtual bool shouldBeVisible(ViewFrame* frame) override;
	virtual void wheelEvent(QWheelEvent* e) override;
	void goToReference(const QModelIndex& idx);
	
	virtual void OnTagAdded(BinaryNinja::BinaryView* data, BinaryNinja::Ref<BinaryNinja::Tag> tag) override;
	virtual void OnTagRemoved(BinaryNinja::BinaryView* data, BinaryNinja::Ref<BinaryNinja::Tag> tag) override;
	virtual void OnTagUpdated(BinaryNinja::BinaryView* data, BinaryNinja::Ref<BinaryNinja::Tag> tag) override;

private Q_SLOTS:
	void hoverTimerEvent();
	void referenceActivated(const QModelIndex& idx);

public:
	TagList(ViewFrame* view, BinaryViewRef data);
	virtual ~TagList();

	void updateTags();
	void navigateToNext();
	void navigateToPrev();

	bool hasSelection();
};
